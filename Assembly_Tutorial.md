# De-novo assembly of a _Wolbachia_ genome

This document contains instructions for generating a de-novo assembly of a _Wolbachia_ genome. 

I recommend that you clone this repository to your local computer, and open up this document in a text editor. That way you can save any changes you make to the code in this tutorial (like file paths).


## 0. Log onto the hummingbird server and create a project directory

You can access the hummingbird server with your UCSC username and Gold password. Please see the humming bird wiki on ["Getting Started"](https://hummingbird.ucsc.edu/getting-started/) for more details. (Feel free to run this analysis on your local computer if you prefer, but note that we may not be familiar with your operating system if you need help.)

Open your terminal and type:
```
ssh <your_cruzid>@hb.ucsc.edu
```

You should be in your home directory. You can check the directory you are in by typing `pwd`. This stands for "print working directory" Mine looks like this:
```
[jomojaco@hb ~]$ pwd
/hb/home/jomojaco
```

Create a new folder in your home directory for this analysis. Its good practice to keep your directories well organized.
```
mkdir genome_assembly
```

Change into this new directory for the rest of the analysis
```
cd genome_assembly
```

> Note: If you are new to linux commands, please refer to the [provided reference slides](https://docs.google.com/presentation/d/1hjIfozfQkjL4gj1eUtvBqgzpWERAkF8Uw43ToAQSxa8/edit#slide=id.p)  

## 1. Access the fastq files produced by the Guppy basecaller

The fastq file we will be working with in that directory is called `wWil.merged.fastq.gz`. Make sure you're still in your directory (the the `~` indicates your home directory, where your directory is located). We are going to create a link to the fastq file into your folder (the `.` indicates the current directory, which is genome_assembly):
```
# create a soft link to the file using the name of the file
ln -s /hb/home/jomojaco/russelllab_tutorial/wWil.filtered.fastq.gz wWil.filtered.fastq.gz
```

Now `ls` and see that `wWil.merged.fastq.gz` has been linked in your directory.

## 2. Running Flye assemble


Next we will use Flye to perform genome assembly. Load the module:
```
module load flye
```

The [Flye manual](https://github.com/fenderglass/Flye/blob/flye/docs/USAGE.md) gives a whole list of all the possible parameters we can give Flye. You can also check these by running `flye -h`. Please read through the section in the manual giving descriptions of these parameters [(here)](https://github.com/fenderglass/Flye/blob/flye/docs/USAGE.md#-parameter-descriptions) and make sure you understand why this is the command we need to run:
```
# create output directory for flye
mkdir flye_my_run
```

## Start an interactive slurm job

Before running more computationally intensive commands, you want to reserve space on a node. This is good cluster ettiquite and ensures that we don't back up the hummingbird login node, which could otherwise become slow for other users if everyone runs stuff there. We can do this by submitting a job to slurm, or by starting an interactive job. Here we will start an interactive job, so that you can see what's happening during the assembly process and test things out.

Start an interactive job (that will last for 5 hours) by running:
```
## create a screen so that we can leave our job running 
screen -S genome_assembly

## run flye on the instruction partition 
salloc --partition=instruction --time=05:00:00 --mem=4G --tasks=1 --cpus-per-task=1 srun flye --nano-hq wWil.filtered.fastq.gz -t 1 --out-dir flye_my_run # run flye assembler 
```
Now while this is running you can use ctrl+a+d to exit your screen and reattach with `screen -r genome_assembly`

If you want, you can see what all the options mean by running `salloc -h`, or visiting [this humminbird tutorial](https://hummingbird.ucsc.edu/documentation/getting-an-interactive-allocation-for-instructional-use/).

Please remember to start interactive jobs (or submit a job to slurm) whenever you're downloading files, installing/running tools, etc!

Once you are done running things, you can end the interactive job by running `exit`, which will end the job and return you to the login node. Or, the job will end once it reaches the time limit, but try to remember to exit when you're done. For now though, leave it running as you move onto the next step.

> Note: Flye took me about 3 hours to run on one thread.

Take a look at the output of Flye
```
cd flye; ls
```

You should see the following files in your directory
```
[aanakamo@hb flye]$ ls
00-assembly   30-contigger    assembly_graph.gfa  flye.log
10-consensus  40-polishing    assembly_graph.gv   params.json
20-repeat     assembly.fasta  assembly_info.txt
```

Consult the Flye manual about what these files represent. Which one contains the assembly? Discuss these files as a group.
> Hint: take a look in `assembly_info.txt`  

All of the tools we will be using for the assembly portion of this tutorial are available as modules on hummingbird. Each module contains the exact dependencies needed for running the particular tool, and these can sometimes conflict if you have more than one module loaded (doesn't always happen, but it's a good habit to keep only modules you need loaded). So, lets unload `Flye` before moving on.
```
module unload flye
```

## 3. Assembly quality control

We will use the tools [Quast](https://quast.sourceforge.net/docs/manual.html#sec2.1) and [BUSCO](https://busco.ezlab.org/busco_userguide.html) to assess the quality of our genome assembly.

Load the module:
```
module load quast
```
Running Quast:
```
mkdir quast
salloc --partition=instruction --time=05:00:00 --mem=4G --tasks=1 --cpus-per-task=1 srun quast flye_my_run/assembly.fasta --nanopore wWil.filtered.fastq.gz -t 1 -o quast --circos --k-mer-stats --glimmer --conserved-genes-finding --rna-finding --est-ref-size 1200000
```
> Quast took me about 20 minutes to run on 1 thread.  

Take some time to research the metrics and figures that QUAST produces, and discuss as a group. Which ones are informative about the quality of our assembly?

- [Quast Github](https://github.com/ablab/quast)
- [Quast Manual](https://quast.sourceforge.net/docs/manual.html#sec2.1)

I would reccommend downloading the quast output to your personal computer, so you can open all the figures it produces. To do this, open a new terminal window (on your personal computer, NOT on hummingbird) and run the following command (replace `{username}` with yours)

```
scp -r {username}@hb.ucsc.edu:/hb/home/{username}/bootcamp2024/quast/ .
```
Load the module:
```
module load busco
```
Running BUSCO:
```
# go back to your directory
mkdir busco
salloc --partition=instruction --time=30:00:00 --mem=8G --tasks=1 --cpus-per-task=4 busco -i flye_my_run/assembly.fasta -l rickettsiales_odb10 -o busco_rickettsiales -m genome --cpu 4 --out_path busco/
```
> BUSCO typically takes 15-30 minutes to run with the rickettsiales_odb10 database on 4 threads, depending on assembly size and completeness.

The rickettsiales_odb10 database is particularly appropriate for Wolbachia genomes since _Wolbachia_ belongs to the order _Rickettsiales_. This will assess genome completeness based on conserved single-copy orthologs expected in rickettsial genomes.

What do the metrics and plots output by Quast tell us about the quality and completeness of our assembly? Do we have enough information to say whether our assembly is "good"?

Good next steps include polishing the assembly with polca, medaka, or racon. These tools can use short or long reads for polishing. To compare the quality of the polished reads, you should use BUSCO with rickettsiales_odb10 database. If you get stuck, you can refer to the methods listed in Jacobs et al 2024 which detail the assembly of the _w_Wil strain of _Wolbachia_.
