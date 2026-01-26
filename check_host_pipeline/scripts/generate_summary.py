# scripts/generate_summary.py

import pandas as pd
import sys
import statistics
from pathlib import Path

# Parse inputs
sample = snakemake.params.sample
idxstats_file = snakemake.input.idxstats
organisms = snakemake.params.organisms
ref_dict = snakemake.params.ref_dict
avg_read_length = snakemake.params.avg_read_length
results_dir = Path(snakemake.output.summary).parent

def parse_depth_file(depth_file):
    """Calculate depth statistics from samtools depth output"""
    depths = []
    try:
        with open(depth_file, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    depth = int(parts[2])
                    if depth > 0:  # Only consider covered positions
                        depths.append(depth)
    except FileNotFoundError:
        return {'mean_depth': 0, 'median_depth': 0, 'covered_bases': 0}
    
    if not depths:
        return {'mean_depth': 0, 'median_depth': 0, 'covered_bases': 0}
    
    return {
        'mean_depth': statistics.mean(depths),
        'median_depth': statistics.median(depths),
        'covered_bases': len(depths)
    }

# Read idxstats
data = []
with open(idxstats_file) as f:
    for line in f:
        if line.startswith('*'):
            continue
        fields = line.strip().split('\t')
        ref = fields[0]
        length = int(fields[1])
        mapped = int(fields[2])
        unmapped = int(fields[3])
        
        # Extract organism prefix
        if '_' in ref:
            organism = ref.split('_')[0]
        else:
            organism = 'unknown'
        
        data.append({
            'organism': organism,
            'contig': ref,
            'length': length,
            'mapped_reads': mapped,
            'unmapped_reads': unmapped
        })

df = pd.DataFrame(data)

# Summarize by organism
summary = df.groupby('organism').agg({
    'mapped_reads': 'sum',
    'unmapped_reads': 'sum',
    'length': 'sum'
}).reset_index()

# Add descriptions from config
summary['description'] = summary['organism'].map(
    lambda x: ref_dict.get(x, {}).get('description', 'Unknown')
)

# Calculate statistics
total_mapped = summary['mapped_reads'].sum()
summary['percentage'] = 100 * summary['mapped_reads'] / total_mapped
summary['coverage'] = (summary['mapped_reads'] * avg_read_length) / summary['length']

# Add depth statistics for each organism
depth_stats_list = []
for org in summary['organism']:
    depth_file = results_dir / 'split' / f'{org}.depth.txt'
    depth_stats = parse_depth_file(depth_file)
    depth_stats_list.append(depth_stats)

depth_df = pd.DataFrame(depth_stats_list)
summary = pd.concat([summary.reset_index(drop=True), depth_df], axis=1)

# Sort by mapped reads
summary = summary.sort_values('mapped_reads', ascending=False)

# Write summary report
with open(snakemake.output.summary, 'w') as f:
    f.write(f"Identity Check Summary for {sample}\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("Mapping Statistics:\n")
    f.write("-" * 80 + "\n")
    for _, row in summary.iterrows():
        f.write(f"{row['organism']:10s} ({row['description']:30s}): "
                f"{row['mapped_reads']:>10,} reads ({row['percentage']:>5.2f}%) "
                f"| {row['coverage']:>6.1f}x breadth\n")
        f.write(f"{'':10s} {'':32s}  "
                f"Mean depth: {row['mean_depth']:>6.1f}x, "
                f"Median depth: {row['median_depth']:>6.1f}x, "
                f"Covered bases: {row['covered_bases']:>10,}\n")
    
    f.write("\n" + "=" * 80 + "\n")
    f.write(f"Total mapped reads: {total_mapped:,}\n")
    
    # Interpretation
    f.write("\nInterpretation:\n")
    f.write("-" * 80 + "\n")
    
    # Find most abundant host and Wolbachia
    host_orgs = summary[summary['organism'].str.contains('d[a-z]+', regex=True)]
    wolb_orgs = summary[summary['organism'].str.startswith('w')]
    
    if not host_orgs.empty:
        top_host = host_orgs.iloc[0]
        f.write(f"Primary host: {top_host['organism']} ({top_host['description']}) "
                f"- {top_host['percentage']:.1f}% of reads\n")
        f.write(f"  Coverage: {top_host['coverage']:.1f}x breadth, "
                f"{top_host['mean_depth']:.1f}x mean depth, "
                f"{top_host['median_depth']:.1f}x median depth\n")
        
        # Check for other hosts
        if len(host_orgs) > 1:
            f.write(f"  Alternative hosts detected:\n")
            for _, row in host_orgs.iloc[1:].iterrows():
                if row['percentage'] > 0.1:  # Only report if >0.1%
                    f.write(f"    - {row['organism']} ({row['description']}): "
                            f"{row['percentage']:.2f}% ({row['mean_depth']:.1f}x mean depth)\n")
    
    if not wolb_orgs.empty:
        top_wolb = wolb_orgs.iloc[0]
        f.write(f"Primary Wolbachia: {top_wolb['organism']} ({top_wolb['description']}) "
                f"- {top_wolb['percentage']:.1f}% of reads\n")
        f.write(f"  Coverage: {top_wolb['coverage']:.1f}x breadth, "
                f"{top_wolb['mean_depth']:.1f}x mean depth, "
                f"{top_wolb['median_depth']:.1f}x median depth\n")
        
        # Calculate titer (Wolbachia/Host ratio)
        if not host_orgs.empty:
            titer = top_wolb['mapped_reads'] / top_host['mapped_reads']
            f.write(f"Estimated titer: {titer:.4f} "
                    f"({titer*100:.2f}% Wolbachia/Host)\n")
        
        # Check for other Wolbachia strains
        if len(wolb_orgs) > 1:
            f.write(f"  Alternative Wolbachia strains detected:\n")
            for _, row in wolb_orgs.iloc[1:].iterrows():
                if row['percentage'] > 0.1:  # Only report if >0.1%
                    f.write(f"    - {row['organism']} ({row['description']}): "
                            f"{row['percentage']:.2f}% ({row['mean_depth']:.1f}x mean depth)\n")
    
    # Quality assessment based on depth
    f.write("\nQuality Assessment:\n")
    f.write("-" * 80 + "\n")
    for _, row in summary.iterrows():
        if row['mapped_reads'] > 0:
            if row['mean_depth'] > 10:
                quality = "HIGH"
            elif row['mean_depth'] > 5:
                quality = "MEDIUM"
            elif row['mean_depth'] > 1:
                quality = "LOW"
            else:
                quality = "TRACE"
            
            f.write(f"{row['organism']:10s}: {quality:8s} "
                    f"(mean depth: {row['mean_depth']:.1f}x, "
                    f"breadth: {row['coverage']:.1f}x)\n")
    
    # Conclusion
    f.write("\n" + "=" * 80 + "\n")
    f.write("CONCLUSION:\n")
    if not host_orgs.empty and not wolb_orgs.empty:
        f.write(f"Sample appears to be {top_host['organism']} infected with "
                f"{top_wolb['organism']}\n")
        
        # Add quality note
        if top_wolb['mean_depth'] < 5:
            f.write(f"NOTE: Low Wolbachia depth ({top_wolb['mean_depth']:.1f}x) "
                    f"may indicate contamination or low titer\n")
    elif not host_orgs.empty:
        f.write(f"Sample appears to be {top_host['organism']} (no Wolbachia detected)\n")
    else:
        f.write("WARNING: Could not determine host/Wolbachia identity\n")

# Write TSV for plotting
summary.to_csv(snakemake.output.tsv, sep='\t', index=False)