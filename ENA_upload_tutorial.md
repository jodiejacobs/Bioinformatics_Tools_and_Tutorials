# Complete Guide to ENA Submissions Using Webin-CLI

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Registering Study and Sample](#registering-study-and-sample)
4. [Submitting Sequencing Reads](#submitting-sequencing-reads)
5. [Submitting Genome Assemblies](#submitting-genome-assemblies)
6. [Submitting Annotated Genomes](#submitting-annotated-genomes)
7. [Troubleshooting](#troubleshooting)
8. [Verification and Monitoring](#verification-and-monitoring)

---

## Prerequisites

### Required Information
Before starting, gather:
- Webin account credentials (register at https://www.ebi.ac.uk/ena/submit/webin/)
- Sample metadata (organism, collection location/date, host information)
- Sequencing files (FASTQ format, gzipped)
- Assembly files (FASTA format for unannotated, EMBL/GenBank for annotated)

### File Requirements
- **All FASTQ files**: Must be gzipped (`.fastq.gz`)
- **All FASTA files**: Must be gzipped (`.fasta.gz`)
- **Annotation files**: EMBL (`.embl.gz`) or GenBank (`.gbk.gz`) format

---

## Environment Setup

### Step 1: Create Mamba Environment

```bash
# Create a new environment
mamba create -n ena_submit

# Activate the environment
mamba activate ena_submit

# Install Java (required for Webin-CLI)
mamba install -c conda-forge openjdk=17

# Verify Java installation
java -version
```

You should see output like: `openjdk version "17.x.x"`

---

### Step 2: Download Webin-CLI

```bash
# Create submission directory
mkdir -p ~/ena_submission
cd ~/ena_submission

# Check available versions
curl -s https://api.github.com/repos/enasequence/webin-cli/releases | grep "tag_name"

# Download specific version (e.g., 9.0.0)
wget https://github.com/enasequence/webin-cli/releases/download/9.0.0/webin-cli-9.0.0.jar

# Rename for convenience
mv webin-cli-9.0.0.jar webin-cli.jar

# Test it works
java -jar webin-cli.jar -version
```

---

## Registering Study and Sample

### Register via Webin Portal

**These must be done BEFORE submitting sequencing data.**

#### 1. Register Study (Project)

1. Log in to: https://www.ebi.ac.uk/ena/submit/webin/
2. Navigate to: **Studies → Register Study**
3. Fill in required fields:
   - Study title
   - Study abstract
   - Study type (typically "Whole Genome Sequencing")
4. **Optional but recommended**: Add locus tag prefix if you plan to submit annotations
5. Submit and save your **PRJEB** accession

#### 2. Register Sample

1. Navigate to: **Samples → Register Samples**
2. Download appropriate checklist spreadsheet:
   - For bacteria: "ENA prokaryote" or "ENA bacteria"
3. Fill in the spreadsheet:

**Required fields:**
- `sample_alias`: Unique identifier (e.g., `wRi_Merrill_23`)
- `tax_id` or `scientific_name`: NCBI taxonomy ID or organism name
- `collection date`: YYYY-MM-DD, YYYY-MM, or YYYY format
- `geographic location`: Country and region

**Recommended fields:**
- `host scientific name`: For symbionts/pathogens
- `isolation_source`: Where DNA was extracted from
- `lat_lon`: Coordinates in format "DD.DDDD N/S DD.DDDD E/W"
- `strain`: Strain designation
- `isolate`: Isolate name

4. Upload spreadsheet and save your **SAMEA/ERS** accession

---

## Submitting Sequencing Reads

### Overview

Sequencing reads are submitted using `-context reads` with Webin-CLI.

**Key points:**
- Validate with `-test` flag first
- Files are uploaded during submission (can take hours)
- Each submission creates an ERR (run) and ERX (experiment) accession

---

### Illumina Paired-End Reads

#### Step 1: Generate MD5 Checksums

```bash
cd /path/to/your/fastq/files

# Generate checksums
md5sum sample_R1.fastq.gz
md5sum sample_R2.fastq.gz

# Or save to file
md5sum *.fastq.gz > checksums.txt
cat checksums.txt
```

#### Step 2: Create Manifest File

```bash
cd ~/ena_submission
nano illumina_manifest.txt
```

**Manifest content:**
```
STUDY       PRJEB123456
SAMPLE      ERS12345678
NAME        sample_illumina_run1
PLATFORM    ILLUMINA
INSTRUMENT  Illumina NovaSeq X Plus
INSERT_SIZE 300
LIBRARY_SOURCE  GENOMIC
LIBRARY_SELECTION  RANDOM
LIBRARY_STRATEGY  WGS
FASTQ       sample_R1.fastq.gz
FASTQ       sample_R2.fastq.gz
```

**Field explanations:**
- `STUDY`: Your PRJEB accession
- `SAMPLE`: Your ERS or SAMEA accession
- `NAME`: Unique run identifier (you choose)
- `PLATFORM`: ILLUMINA, OXFORD_NANOPORE, PACBIO_SMRT, etc.
- `INSTRUMENT`: Exact sequencer model (see valid list below)
- `INSERT_SIZE`: Average insert size in bp (typically 300-500 for WGS)
- `LIBRARY_SOURCE`: GENOMIC, TRANSCRIPTOMIC, METAGENOMIC, etc.
- `LIBRARY_SELECTION`: RANDOM (fragmentation), PCR, PolyA, etc.
- `LIBRARY_STRATEGY`: WGS, RNA-Seq, AMPLICON, etc.
- `FASTQ`: Filename(s) - list R1, then R2

**Valid INSTRUMENT values for Illumina:**
- Illumina Genome Analyzer, Illumina Genome Analyzer II
- Illumina HiSeq 2000, Illumina HiSeq 2500, Illumina HiSeq 4000
- Illumina MiSeq, Illumina MiniSeq
- Illumina NovaSeq 6000, Illumina NovaSeq X, Illumina NovaSeq X Plus
- NextSeq 500, NextSeq 550, NextSeq 1000, NextSeq 2000

#### Step 3: Validate (Test Mode)

```bash
java -jar webin-cli.jar \
  -context reads \
  -userName Webin-XXXXX \
  -password YOUR_PASSWORD \
  -manifest illumina_manifest.txt \
  -inputDir /path/to/fastq/files \
  -outputDir ./webin_output \
  -validate \
  -test
```

**What this does:**
- Validates FASTQ format and quality
- Checks metadata
- Does NOT upload files
- Does NOT create submission
- Creates validation report in `webin_output/`

#### Step 4: Check Validation Report

```bash
cat webin_output/reads/sample_illumina_run1/validate/webin-cli.report
```

**Look for:**
- "Submission(s) validated successfully" = good to proceed
- Any ERROR messages = must fix before submitting

**Common validation errors:**
- File not found: Check `-inputDir` path
- Invalid FASTQ format: Ensure files are properly gzipped
- Invalid sample/study: Check accessions are correct
- Invalid INSTRUMENT: Use exact name from valid list

#### Step 5: Submit for Real

**Once validation passes:**

```bash
java -jar webin-cli.jar \
  -context reads \
  -userName Webin-XXXXX \
  -password YOUR_PASSWORD \
  -manifest illumina_manifest.txt \
  -inputDir /path/to/fastq/files \
  -outputDir ./webin_output \
  -submit
```

**Note:** Removed `-test` flag and changed `-validate` to `-submit`

**This will:**
- Upload FASTQ files to ENA (takes time!)
- Submit metadata
- Assign ERR (run) and ERX (experiment) accessions

#### Step 6: Save Accession Numbers

```bash
# View submission receipt
cat webin_output/reads/sample_illumina_run1/submit/webin-cli.report

# Find accessions
grep -E "ERR|ERX" webin_output/reads/sample_illumina_run1/submit/webin-cli.report

# Save to file
echo "Illumina Run: ERR12345678" >> submission_accessions.txt
echo "Illumina Experiment: ERX12345678" >> submission_accessions.txt
```

---

### Nanopore Reads

**Process is nearly identical to Illumina, but:**

#### Manifest Differences

```
STUDY       PRJEB123456
SAMPLE      ERS12345678
NAME        sample_nanopore_run1
PLATFORM    OXFORD_NANOPORE
INSTRUMENT  MinION
LIBRARY_SOURCE  GENOMIC
LIBRARY_SELECTION  RANDOM
LIBRARY_STRATEGY  WGS
FASTQ       sample_nanopore.fastq.gz
```

**Key differences:**
- `PLATFORM`: OXFORD_NANOPORE
- `INSTRUMENT`: MinION, GridION, or PromethION
- Only ONE `FASTQ` line (Nanopore is single-end)

**Valid Nanopore INSTRUMENT values:**
- MinION
- GridION
- PromethION

**All other steps (validation, submission) are identical to Illumina.**

---

### Important Notes for Read Submissions

#### File Upload Takes Time
- Large files (10+ GB) can take several hours to upload
- Consider running in a screen session or SLURM job
- Progress is shown during upload

#### Test vs Production Servers
- Test server may not recognize newly created studies/samples
- If validation fails with `-test`, try without it (production mode)
- Test submissions are deleted daily at 3 AM GMT

#### Multiple Runs for Same Sample
- You can submit multiple sequencing runs for the same sample
- Use different `NAME` values for each run
- All will link to the same sample and study

---

## Submitting Genome Assemblies

### Overview

Genome assemblies are submitted using `-context genome` with Webin-CLI.

**Two types:**
1. **Unannotated assemblies**: FASTA file only
2. **Annotated assemblies**: EMBL or GenBank file with gene annotations

---

### Unannotated Assembly

#### Step 1: Prepare Assembly File

```bash
# Ensure FASTA is gzipped
gzip assembly.fasta

# Or if already gzipped
ls -lh assembly.fasta.gz
```

#### Step 2: Create Chromosome List (for complete genomes)

**Required if you have a complete genome (not draft contigs).**

Create `chromosome_list.txt`:

```
sequence_name	chromosome_name	chromosome_type
```

**Example for circular bacterial chromosome:**
```
wRi_chromosome	wRi_chromosome	Circular-Chromosome
```

**Format rules:**
- Tab-separated (NOT spaces)
- Column 1: Sequence name from FASTA header (after `>`)
- Column 2: Object name (chromosome identifier)
- Column 3: Topology type

**Valid chromosome types:**
- Circular-Chromosome
- Linear-Chromosome
- Plasmid
- Circular-Plasmid
- Linear-Plasmid

**Then compress:**
```bash
gzip chromosome_list.txt
```

**Note:** If you have a draft assembly with multiple contigs, you typically don't need a chromosome list file.

#### Step 3: Create Manifest File

```bash
nano genome_manifest.txt
```

**Manifest content:**
```
STUDY           PRJEB123456
SAMPLE          ERS12345678
ASSEMBLYNAME    organism_v1
ASSEMBLY_TYPE   isolate
COVERAGE        100
PROGRAM         Flye
PLATFORM        OXFORD_NANOPORE
MINGAPLENGTH    10
MOLECULETYPE    genomic DNA
FASTA           assembly.fasta.gz
CHROMOSOME_LIST chromosome_list.txt.gz
```

**Field explanations:**
- `STUDY`: Your PRJEB accession
- `SAMPLE`: Your ERS or SAMEA accession
- `ASSEMBLYNAME`: Unique assembly name (you choose)
- `ASSEMBLY_TYPE`: isolate, clone, or primary metagenome
- `COVERAGE`: Estimated sequencing depth
- `PROGRAM`: Assembly software used (Flye, Canu, SPAdes, etc.)
- `PLATFORM`: Sequencing platform (ILLUMINA, OXFORD_NANOPORE, PACBIO_SMRT)
- `MINGAPLENGTH`: Minimum gap length (10 is typical)
- `MOLECULETYPE`: genomic DNA, genomic RNA, viral cRNA
- `FASTA`: Your assembly filename
- `CHROMOSOME_LIST`: Chromosome list filename (omit if draft assembly)

**Optional field:**
- `RUN_REF`: Link to read runs (e.g., `ERR123456,ERR123457`)

#### Step 4: Copy Files to Submission Directory

```bash
# Copy FASTA and chromosome list
cp /path/to/assembly.fasta.gz ~/ena_submission/
cp /path/to/chromosome_list.txt.gz ~/ena_submission/
```

#### Step 5: Validate

```bash
cd ~/ena_submission

java -jar webin-cli.jar \
  -context genome \
  -userName Webin-XXXXX \
  -password YOUR_PASSWORD \
  -manifest genome_manifest.txt \
  -inputDir ~/ena_submission \
  -outputDir ./webin_output \
  -validate
```

**Note:** Genome submissions often work better without `-test` flag

#### Step 6: Check Validation Report

```bash
cat webin_output/genome/organism_v1/validate/webin-cli.report
```

**Common errors:**

**"Invalid number of sequences: 1, Minimum number of sequences for CONTIG is: 2"**
- Solution: Add chromosome list file (you have a complete genome, not contigs)

**"The qualifier 'strain' must exist when qualifier 'sub_strain' exists"**
- Solution: Edit sample in Webin Portal to ensure both strain and sub_strain are present (or remove sub_strain)

**"File not found"**
- Solution: Ensure FASTA and chromosome list are in `-inputDir`

#### Step 7: Submit

```bash
java -jar webin-cli.jar \
  -context genome \
  -userName Webin-XXXXX \
  -password YOUR_PASSWORD \
  -manifest genome_manifest.txt \
  -inputDir ~/ena_submission \
  -outputDir ./webin_output \
  -submit
```

#### Step 8: Save Accession

```bash
# Find ERZ accession
grep "ERZ" webin_output/genome/organism_v1/submit/webin-cli.report

# Save it
echo "Genome Assembly: ERZ12345678" >> submission_accessions.txt
```

**Note:** You'll also receive a GCA accession after processing (2-7 days)

---

## Submitting Annotated Genomes

### Overview

Annotated genomes require:
1. **Registered locus tag prefix** (must request from ENA)
2. **Annotation file in EMBL or GenBank format**
3. **Chromosome list file**

---

### Step 1: Register Locus Tag Prefix

**CRITICAL: This must be done BEFORE submitting annotations.**

#### Option A: During Study Registration

When registering a study in Webin Portal, look for:
- "Locus Tag Prefix" field
- Or "Project Attributes" section
- Suggest your preferred prefix (e.g., "WRI", "MYORG")

#### Option B: Request After Study Creation

Email: **datasubs@ebi.ac.uk**

```
Subject: Request locus tag prefix for study PRJEB123456

Dear ENA Support,

I would like to request a locus tag prefix for my study to submit 
an annotated genome assembly.

Study accession: PRJEB123456
Study title: [Your study title]
Webin account: Webin-XXXXX
Organism: [Organism name]

Suggested locus tag prefix: WRI

Number of prefixes needed: 1

Thank you,
[Your name]
[Institution]
```

**Response time:** 1-2 business days

**Important:** After receiving the prefix, wait 24 hours before submitting for it to propagate in ENA's system.

---

### Step 2: Prepare Annotation File

#### If You Have Prokka Output

Prokka generates `.gbk` files with auto-assigned locus tags (e.g., `PROKKA_00001`).

**Replace Prokka's locus tags with your registered prefix:**

```bash
# Example: Replace PROKKA_ with WRI_
sed 's/PROKKA_/WRI_/g' prokka_output.gbk > annotated.gbk
```

#### Fix Common GenBank Format Issues

**Check LOCUS line:**
```bash
head -n 1 annotated.gbk
```

Should look like:
```
LOCUS       sequence_name 1234567 bp    DNA     circular BCT 01-JAN-2026
```

**Common issues:**
- Missing space between name and length
- Says "linear" instead of "circular" for bacterial chromosomes
- Missing "BCT" (bacteria) division code

**Fix with:**
```bash
# Fix missing space (if name and length are stuck together)
sed -i '1s/sequence_name1234567/sequence_name 1234567/' annotated.gbk

# Fix topology
sed -i '1s/linear/circular/' annotated.gbk

# Add BCT division
sed -i '1s/DNA     circular/DNA     circular BCT/' annotated.gbk

# Remove trailing spaces from locus tags
sed -i 's/locus_tag="\(WRI_[0-9]*\) "/locus_tag="\1"/g' annotated.gbk
```

#### Convert GenBank to EMBL Format

**ENA prefers EMBL format.**

Using BioPython:
```bash
python3 << 'EOF'
from Bio import SeqIO
SeqIO.convert('annotated.gbk', 'genbank', 'annotated.embl', 'embl')
print("Conversion complete!")
EOF
```

**If conversion fails**, you can try submitting the GenBank file directly (ENA accepts both).

#### Compress the File

```bash
gzip annotated.embl
# or
gzip annotated.gbk
```

---

### Step 3: Create Chromosome List

**Same as for unannotated assembly.**

```bash
nano chromosome_list.txt
```

Content (tab-separated):
```
sequence_name	chromosome_name	Circular-Chromosome
```

```bash
gzip chromosome_list.txt
```

---

### Step 4: Create Manifest

```bash
nano annotated_manifest.txt
```

**Content:**
```
STUDY           PRJEB123456
SAMPLE          ERS12345678
ASSEMBLYNAME    organism_v1_annotated
ASSEMBLY_TYPE   isolate
COVERAGE        100
PROGRAM         Flye
PLATFORM        OXFORD_NANOPORE
MINGAPLENGTH    10
MOLECULETYPE    genomic DNA
FLATFILE        annotated.embl.gz
CHROMOSOME_LIST chromosome_list.txt.gz
```

**Key difference from unannotated:**
- Use `FLATFILE` instead of `FASTA`
- File is `.embl.gz` or `.gbk.gz` (not `.fasta.gz`)

---

### Step 5: Copy Files and Submit

```bash
# Copy files
cp annotated.embl.gz ~/ena_submission/
cp chromosome_list.txt.gz ~/ena_submission/

cd ~/ena_submission

# Validate
java -jar webin-cli.jar \
  -context genome \
  -userName Webin-XXXXX \
  -password YOUR_PASSWORD \
  -manifest annotated_manifest.txt \
  -inputDir ~/ena_submission \
  -outputDir ./webin_output \
  -validate

# If validation passes, submit
java -jar webin-cli.jar \
  -context genome \
  -userName Webin-XXXXX \
  -password YOUR_PASSWORD \
  -manifest annotated_manifest.txt \
  -inputDir ~/ena_submission \
  -outputDir ./webin_output \
  -submit
```

---

### Common Annotation Submission Errors

**"locus_tag prefix 'WRI' is not registered with the project"**
- Locus tag not yet registered or not propagated
- Wait for ENA email confirmation
- Wait additional 24 hours after confirmation
- Try editing study XML (advanced, may not work)

**"Illegal locus_tag value"**
- Check for trailing spaces in locus tags
- Ensure tags match format: PREFIX_00001 (no spaces)

**"Feature table validation failed"**
- Check annotation file format
- Ensure all features have required qualifiers
- Verify protein translations are valid

---

## Troubleshooting

### General Issues

#### "Unable to write to output directory"
```bash
# Create the directory
mkdir -p webin_output
chmod 755 webin_output
```

#### "Unknown study/sample"
- Verify accessions are correct (PRJEB vs ERP, SAMEA vs ERS)
- Try using alternate accession format
- For new studies, try without `-test` flag (production server)
- Ensure study/sample are in YOUR Webin account

#### "Invalid INSTRUMENT field value"
- Use exact instrument name from ENA's valid list
- Add `PLATFORM` field explicitly (e.g., `PLATFORM    ILLUMINA`)
- Check for extra spaces or typos

#### File Upload Slow or Stalling
- Check network/firewall allows FTP to webin.ebi.ac.uk
- For faster uploads, install Aspera and use `-ascp` flag
- Run in screen session for long uploads

---

### Validation Errors

#### "Invalid FASTQ format"
```bash
# Check file is properly gzipped
file reads.fastq.gz

# Test decompression
zcat reads.fastq.gz | head -n 4

# Check quality score encoding (should be Phred+33)
zcat reads.fastq.gz | head -n 4
```

#### "Read names don't match between pairs"
```bash
# Check R1 read names
zcat R1.fastq.gz | grep "^@" | head -n 5

# Check R2 read names
zcat R2.fastq.gz | grep "^@" | head -n 5

# They should match (except for /1 or /2 suffix)
```

#### "Sample taxonomy must be species rank or below"
- Change sample `tax_id` to species or strain level
- Cannot use genus-level taxonomy for assemblies

---

### Assembly-Specific Issues

#### "Assembly too short/too long"
- ENA has size limits for different assembly types
- Verify your sequences are correct
- Check for contamination if assembly is too long

#### "Sequence names contain invalid characters"
- Use only alphanumeric characters, underscores, hyphens
- Avoid: spaces, pipes (|), colons (:), special characters
- Rename sequences in FASTA header if needed

---

## Verification and Monitoring

### Check Submission Status in Webin Portal

Log in: https://www.ebi.ac.uk/ena/submit/webin/

#### For Reads:
1. **Raw Reads → Runs Report**: See all submitted runs and their accessions
2. **Raw Reads → Run Files Report**: Check file upload and processing status
3. **Raw Reads → Run Processing Report**: Monitor analysis pipeline progress

#### For Assemblies:
1. **Genome Assemblies → Assembly Report**: See submitted assemblies
2. Check processing status

---

### Timeline for Public Availability

**After submission:**

| Step | Timeline | What Happens |
|------|----------|--------------|
| Immediate | Seconds | Accessions assigned (ERR, ERX, ERZ) |
| File Processing | 24-48 hours | FASTQ files validated, QC metrics calculated |
| Assembly Processing | 3-7 days | Assembly analyzed, GCA accession assigned |
| Public Release | Set by you | Data becomes publicly searchable |
| INSDC Sync | 1-2 weeks | Data synced to GenBank and DDBJ |

**Note:** These are calendar days, not business days. ENA processes submissions 24/7.

---

### Accession Number Types

| Type | Format | What It Represents | When Assigned |
|------|--------|-------------------|---------------|
| PRJEB | PRJEB123456 | Study/Project | Study registration |
| ERP | ERP123456 | Study (alternate format) | Study registration |
| SAMEA | SAMEA123456789 | Sample | Sample registration |
| ERS | ERS12345678 | Sample (alternate format) | Sample registration |
| ERR | ERR12345678 | Sequencing Run | Read submission |
| ERX | ERX12345678 | Experiment | Read submission |
| ERZ | ERZ12345678 | Analysis/Assembly | Assembly submission |
| GCA | GCA_123456789.1 | Genome Assembly | After assembly processing |

**Use in publications:**
- Study: PRJEB accession
- Sample: SAMEA accession
- Reads: ERR accessions
- Assembly: GCA accession (once assigned)

---

## Running in SLURM Jobs

For large file submissions, use SLURM to avoid interruptions:

```bash
#!/bin/bash
#SBATCH --job-name=ena_submit
#SBATCH --time=8:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1
#SBATCH --output=ena_submit_%j.log

# Activate environment
eval "$(conda shell.bash hook)"
mamba activate ena_submit

# Set variables
WEBIN_CLI="/home/username/ena_submission/webin-cli.jar"
USERNAME="Webin-XXXXX"
PASSWORD="YOUR_PASSWORD"
MANIFEST="/home/username/ena_submission/manifest.txt"
INPUT_DIR="/path/to/files"
OUTPUT_DIR="/home/username/ena_submission/webin_output"
CONTEXT="reads"  # or "genome"

# Submit
java -jar $WEBIN_CLI \
  -context $CONTEXT \
  -userName $USERNAME \
  -password $PASSWORD \
  -manifest $MANIFEST \
  -inputDir $INPUT_DIR \
  -outputDir $OUTPUT_DIR \
  -submit

echo "Submission complete! Check output directory for receipt."
```

Submit with:
```bash
sbatch submit_ena.sh
```

---

## Best Practices

### Before Submitting
- [ ] Register study and sample first
- [ ] Request locus tag prefix if submitting annotations
- [ ] Generate MD5 checksums for all files
- [ ] Compress all files with gzip
- [ ] Validate in test mode first
- [ ] Check validation reports carefully

### During Submission
- [ ] Use screen or SLURM for large uploads
- [ ] Monitor progress
- [ ] Save all accession numbers immediately
- [ ] Keep local copies of manifest files

### After Submission
- [ ] Verify in Webin Portal
- [ ] Check processing reports
- [ ] Wait for GCA accession (assemblies)
- [ ] Set appropriate release date
- [ ] Update publications with accessions

---

## Quick Reference

### Common Commands

```bash
# Activate environment
mamba activate ena_submit

# Validate reads (test mode)
java -jar webin-cli.jar -context reads -userName Webin-X -password P \
  -manifest reads.txt -inputDir /path -outputDir ./output -validate -test

# Submit reads (production)
java -jar webin-cli.jar -context reads -userName Webin-X -password P \
  -manifest reads.txt -inputDir /path -outputDir ./output -submit

# Validate genome
java -jar webin-cli.jar -context genome -userName Webin-X -password P \
  -manifest genome.txt -inputDir /path -outputDir ./output -validate

# Submit genome
java -jar webin-cli.jar -context genome -userName Webin-X -password P \
  -manifest genome.txt -inputDir /path -outputDir ./output -submit

# Check version
java -jar webin-cli.jar -version

# Get help
java -jar webin-cli.jar -help
```

### Useful Resources

- **ENA Documentation**: https://ena-docs.readthedocs.io/
- **Webin Portal**: https://www.ebi.ac.uk/ena/submit/webin/
- **ENA Browser**: https://www.ebi.ac.uk/ena/browser/
- **Webin-CLI GitHub**: https://github.com/enasequence/webin-cli
- **ENA Helpdesk**: datasubs@ebi.ac.uk
- **NCBI Taxonomy**: https://www.ncbi.nlm.nih.gov/Taxonomy/

### Contact Information

**For submission issues, questions, or help:**
- Email: datasubs@ebi.ac.uk
- Include: Webin account, accession numbers, error messages
- Response time: Usually 1-2 business days

---

## Summary Workflow

```
1. Register in Webin Portal
   ├── Create study (get PRJEB)
   ├── Register samples (get SAMEA/ERS)
   └── Request locus tags (if annotating)

2. Prepare Files
   ├── Generate MD5 checksums
   ├── Compress with gzip
   └── Create manifests

3. Submit Reads
   ├── Validate with -test
   ├── Fix any errors
   └── Submit (get ERR/ERX)

4. Submit Assembly
   ├── Create chromosome list (if needed)
   ├── Validate
   └── Submit (get ERZ, later GCA)

5. Submit Annotations (optional)
   ├── Wait for locus tag registration
   ├── Replace locus tags in file
   ├── Convert to EMBL
   └── Submit (get new ERZ)

6. Monitor & Verify
   ├── Check Webin Portal
   ├── Wait for processing
   └── Data goes public on release date
```

---

**End of Guide**

