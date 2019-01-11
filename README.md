Fully-Bayesian unfolding framework based on Python3 using PyMC3 library for Markow-Chain sampling. All of the tools below have been tested using CERN LCG software from cvmfs. It should work on lxplus, but also anywhere else where you have access to cvmfs and can use 'lsetup'.

## Table of Contents
1.   [Setup](#setup)
2.   [Examples for running FBU](#examples-for-running-fbu)
     * [Inpus structure and program flow](#inputs-structure-and-program-flow)
     * [Preparing JSON inputs for FBU](#preparing-json-inputs-for-fbu)
        * [Examples how to create JSON inputs](#examples-how-to-create-json-inputs)
        * [Obtaining truth AC values](#obtaining-truth-ac-values)
     * [Running FBU with created JSON inputs](#running-fbu-with-created-json-inputs)

# Setup

## Dependencies
The current setup assumes that you have access to cvmfs and the lcg software via /cvmfs/sft.cern.ch repository. We use `python3`, `ROOT` and `numpy` from lcg -- other dependencies are installed using `pip`.

## Initial setup

Clone the repo
~~~{.sh}
git clone git@github.com:clementhelsens/UEttbar_unfolding.git
cd UEttbar_unfolding
~~~

Install software + create virtual python environment (venv). Everything is done automatically using `install.sh` script:
~~~{.sh}
source install.sh x86_64-slc6-gcc62-opt
~~~
Where `x86_64-slc6-gcc62-opt` is the architecture of the system where you are setting things up. The example given works for lxplus, check your architecture (in particular `slc6` vs `slc5`, `centos7`, etc...) for use elsewhere. The `gcc` version is set to `gcc62` which is currently heavily used in recent ASG software releases and also supported by `lcg` software.

## Sourcing FBU environment

For repeated setup environment (use this instead of above installation steps) use `init.sh` script inside `$UNFOLDINGDIR` (assumes you have $ATLAS_LOCAL_ROOT_BASE variable set up):
~~~{.sh}
source init.sh
~~~

# Examples for running FBU

## Inputs structure and program flow
FBU uses inputs in a format of `histos/systematic/region/map_distribution_channel.root`, where the folder structure is as shown (systematics folder e.g. EG_RESOLUTION_ALL__1up, and region subfolders, e.g. resolved_muele, dilepton_emu, etc) and distribution is dy, dypttt, dymtt, dybetatt, i.e. any dY vs X (inclusive or differential) observable to unfold. Channels are typically meant such as b-tag multiplicity, lepton charge sign, etc.

By default the inputs are produced un-rebined (with exception of bootstrapping replicas which would otherwise be unbearably large). The dY vs X double-differential observables are TH2 histograms with differential binning on Y axis and dY binning on X axis. The first step is to rebin the inputs histograms to final format, which is TH1 histograms where differential bins are stacked next to each other. See section on rebinning inputs histograms below.

In addition to rebinning, a number of operations can be performed on these inputs, that *preserve* the folder structure, such that these operations can be applied in various order or omitted. The operations are:

  * Symmetrizing up/down systematic variations
  * Bootstrapping for non-scale-factor systematic variations
  * General pruning of normalization and or shape of systematics

The current consensus is to first perform bootstrapping, then symmetrize up/down variations and finally perform systematics pruning. **NOTE that it is recommended to run symmetrization even if pruning is not used. The symmetrization code has better handling of corner cases such as both up/down shifts changing bin yields in the same direction, etc. These cases are otherwise not properly handeled!**

Finally, JSON based inputs are produced from the above root inputs. The JSON inputs can be combined between channels and regions (note that combining any decay channels such as l+jets and dilepton is not yet possible). The JSON inputs are used by FBU unfolding itself.

## Rebinning input histograms
Inputs for unfolding are assumed to have fine-granularity dY binning (e.g. dY bin width of 0.1) to optimize binning without having to recreate histograms in whatever event loop analysis. Therefore rebinning must be performed:
~~~{.sh}
python python/run_rebin.py path_to_config
~~~
For example of rebin config file, see `config/examples/rebin_config_example.json`. In terms of procedure to optimize binning for as linear response as posssible, see `README_binning_optimization.md`.

## Symmetrizing two-sided systematic shifts
The profile-likelihood approach within FBU assumes a single NP per systematic uncertainty, therefore for two-sided systematic variations some form of symmetrization is expected. The following script is available to symmetrize up/down variations bin-by-bin.
~~~{.sh}
python python/symmetrize_syst.py -i data/histos_rebinned -o data/histos_symmetric config/examples/syst_pruning_example.json
~~~
Use `python python/symmetrize_syst.py --help` for full list of options. In particular, it is possible to specify, if one should take maximum(abs(up), abs(down)) or instead take an average(abs(up), abs(down)). Add `-m` flag to use maximum, otherwise default is to take average.

## Running bootstrapping on systematics
To remove statistically insignificant effects in systematic variations, bootstrapping is employed. There are a couple of prerequisites for this:

1. Non-scale-factor systematic FBU inputs and nominal have stored Poisson replicas for bootstrapping in a TObjArray of TH1x histograms. (The whole procedure can be also used to smooth modeling uncertainties). Scale-factor systematics cannot be bootstrapped, since they are by-definition always statistically significant due to full correlation between nominal and variation (same events used).
2. The bootstrapping replicas have final binning desired -- the rebinning step above does not do replicas rebinning (due to both performance and disk usage constraints -- unrebinned replicas are huuge).

To run bootstrapping use `bootstrapping.C` ROOT macro:
~~~{.sh}
root -l -q -b 'bootstrapping.C("data/histos_rebinned","data/histos_rebinned_bootstrapped",100,2.,false,false,"ljets")'
~~~
Where the first argument is the path to files which should be bootstrapped, second is the the output path, third is the number of bootstrapping replicas used, 2. stands for 2 SD used as a significance criterion. The two bool arguments stand for debugging and debugging plots, respectively. By default these are not produced since it is time consuming. The last argument refers to the channel we are in: "ljets" or "dilep". Default is "ljets".

## Pruning shape and or normalization effects of systematics
In addition to smoothing and removing statistically insignificant systematics via bootstrapping, a general pruning procedure can be employed to remove insignificant systematics. The procedure does following (inspired heavily by TRexFitter):

1. Check for shape effect of a systematic: If at least one bin has a relative shift above specified threshold, keep shape effect, otherwise set shape to nominal (maintaining normalization shift, see point 2.)
2. Check if relative normalization shift of the systematic is above specified threshold. If yes, keep normalization effect, otherwise set systematics normalization effect to be same as nominal.

Example usage of the systematics pruning script:
~~~{.sh}
python python/run_syst_pruning.py -i data/histos -o data/histos_prunned pruning_config.json -n normalization_threshold -s shape_threshold
~~~
Where `-i` and `-o` flags set input and output files location respectively. Normalization and shape thresholds are specified via `-n` and `-m` flags respectively. The values are typically fractions of percent, e.g. 0.001 means 0.1% threshold.

Check the `config/examples/syst_pruning_example.json` example JSON config for usage. In general, this config specifies the systematic variations (what is the folder name for corresponding up/down/nominal shift), 

Additionally, an example bash script is provided, using which it is possible to automate testing of multiple pruning thresholds, in `scripts/examples/submit_syst_pruning_FBU_batch.sh`. This script can prepare pruned inputs and submit a batch job to run unfolding on this pruned setup, and can do so in a loop for specified dY observables and various pruning thresholds. See the documentation provided in the script, and feel free to make a copy of the script and modify as necessary.

## Comparing systematic shifts with respect to nominal histogram
The script run_syst_comparison.py compares systematic shifts with respect to nominal while the config file can be the same as the one used for prunning. The script creates subfolders inside output_dir - one for each region - one for each systematics. 
Example usage of the script for systematic comparison:
~~~{.sh}
python python/run_syst_comparison.py ./config/syst_pruning.json -i data/histos_rebinned -o data/histos_SystComparison
~~~
Where `-i` and `-o` flags set location of input and output directories, respectively.

## Preparing JSON inputs for FBU

**NOTE: JSON inputs production is undergoing significant overhaul in order to allow advanced features such as systematics and backgrounds (de)correlation and combination of independent decay channels. We first present tutorial how to use the new approach. For compatibility reasons, old approach is still available below.**

### New JSON format for (de)correlating systematics and backgrounds accross channels

Example how to produce JSON inputs:
~~~{.sh}
python python/histo2json_combination.py -i 'path_to_data' -o 'path_to_output_json' -v 'map_dymtt', -n 'resolved_boosted_combine12tagQ' -g 'path_to_config_file.json'
~~~
Above script will attempt to produce JSON inputs for FBU, store them in directory specified by `-o` parameter. It will do so for inclusive/differential observable specified ('mtt' in the example above). It is expected that inputs are stored in directory specified by `-i` parameter, with subfolders for individual systematic uncertainties and one sub-folder for truth-level histograms. Individual systematic subfolders should contain subfolders with regions. Regions can be divide into hierarchy of 'regionfolder/sub-region files'. For instance, if one has resolved and boosted regions with various b-tagging multiplicities, it possible to have directories for resolved and boosted with 1-btag and 2-btag files in each of the two region sub-directories.

The output JSON files will be stored with filenames containing a unique suffix specified by `-n` parameter. Use this to distinguish your various configurations. There is no prescribed format or any obligation, you will however need to specify this value to FBU such that it knows which files to load for unfolding.

Special to the new JSON producing script is the new configuration file format. See the example config file with comments in `config/examples/config_unfolding_decorelated.json`. This config file is common to both histo2json_combination.py script as well as the FBU-running script runUnfolding_combination.py.

In particular, the most significant change compared to old approach is that background and systematics now have to specified in named groups (the naming is up to the user). Each group specifies a list of regions in which the background normalization and or systematics should be correlated. The background groups and systematics groups are completely independent, it is possible to re-use names for background groups and for systematics groups without clashes and also possibe to independently decorelate background normalisation while keeping object-based systematics correlated.

Important feature of this design is that it is now possible to combine regions which have different backgrounds and/or systematics such as combining regions in l+jets and dilepton channel. The key is to define groups specific to ljets and dilepton for backgrounds and systematics which exist in one decay channel but not in other. Any backgrounds and systematics that should be correlated must specified in a single common group.


### Old JSON format (backgrounds and systs always correlated, not possible to combine different decay channels)

#### Examples how to create JSON inputs

For the inclusive resolved l+jets channel
~~~{.sh}
python python/histo2json.py -v "map_dy" -s "combine012tagQ" -c "resolved_muele"
~~~
#### For differential observables
~~~{.sh}
python python/histo2json.py -v "map_dymtt" -s "combine012tagQ" -c "resolved_muele"
~~~
#### To combine boosted and resolved l+jets regions
~~~{.sh}
python python/histo2json.py -c "resolved_muele boosted_muele" -s "combine12tagQ combine12tagQ"
~~~
#### For other decay channels, specify different channel and selection, for dilepton for example
~~~{.sh}
python python/hist2json.py -c "dilep_emu" -s "dilep_1tagin"
~~~

In all the examples above, the code assumes, that a configuration file `config_hist2json.json` exists in the `config/` directory. You can specify path to a different configuration file by adding parameter `-g path-to-config` to `hist2json.py` script:
~~~{.sh}
python python/hist2json.py -c "dilep_emu" -s "dilep_1tagin" -g config/my_custom_json_config.json
~~~
Now you have json files in the directory:
~~~{.sh}
data/json/
~~~
#### Obtaining truth AC values
This step is compulsory for linearity studies. The following script calculates the true (parton-level) Ac values for observables specified and for the sample specified (can be any MC prediction, including reweighted asymmetries). The example below is for l+jets ttbar sample with DSID 410470
~~~{.sh}
python python/getTruthAc.py data/histos/truth/map_dy_410470\*
~~~
Then add the values in the json file with truth asymmetries `config/truth_dY.json`

## Running FBU with created JSON inputs

### New approach with systematics and background de-correlation

Example on how to run Asimov unfolding (pseudodata is MC signal+background)
~~~{.sh}
python python/runUnfolding.py -o outputs -s -1 -n 1 -t '' -a 'asimov' -i data/json/ -d 4 -f -e 'name_of_the_region_configuration' -g 'path_to_histo2json_combination_config.json'
~~~
Run `python python/runUnfolding_combination.py --help` for full list of options. The most common ones are:
`-o` path to output directory, where the results and parameter traces will be stored
`-s` seed used by unfolding. If different from -1, Poisson-smear the bins of (pseudo)data, using the specified seed
`-n` number of sub-jobs to run inside the `runUnfolding.py` process instance. Each consequent sub-job will have seed incremented by +1
`-f` store full trace of the sampling, including trace of all bins of the unfolded spectrum.
`-e` name of the region+channel to be unfolded. This is essentially the suffix of individual map_dy_*_ JSON input files produced by `histo2json.py`. The naming can be completely arbitrary, one simply has to just use the same name in histo2json `-n` parameter and in `-e` parameter of runUnfolding.
`-g` path to JSON configuration file for FBU. See `config/examples/config_unfolding_example.json` for available options and their description

## Old approach (systematics and backgrounds cannot be de-correlated)

Example on how to run Asimov unfolding (pseudodata is MC signal+background)
~~~{.sh}
python python/runUnfolding.py -o outputs -s -1 -n 1 -t '' -a 'asimov' -i data/json/ -d 4 -f -e resolved_muelecombine12tagQ_boosted_muelecombine12tagQ -g config_unfolding.json
~~~
Run `python python/runUnfolding.py --help` for full list of options. The most common ones are:
`-o` path to output directory, where the results and parameter traces will be stored
`-s` seed used by unfolding. If different from -1, Poisson-smear the bins of (pseudo)data, using the specified seed
`-n` number of sub-jobs to run inside the `runUnfolding.py` process instance. Each consequent sub-job will have seed incremented by +1
`-f` store full trace of the sampling, including trace of all bins of the unfolded spectrum.
`-e` name of the region+channel to be unfolded. This is essentially the suffix of individual map_dy_*_ JSON input files produced by `histo2json.py`
`-g` path to JSON configuration file for FBU. See `config/examples/config_unfolding_decorelated.json` for available options and their description


### Linearity tests of FBU
To run unfolding with various reweighted signals and check that we are able to unfold these values (linearity test):
~~~{.sh}
python python/runUnfolding.py -o outputs -s -1 -n 1 -t '' -a 'A6neg A4neg A2neg A2pos A4pos A6pos' -i data/json/ -d 4 -f -e resolved_muelecombine12tagQ_boosted_muelecombine12tagQ -g config_unfolding.json
~~~

~~~{.sh}
python python/DrawPosterior.py outputs/AcPosterior_seed-1_resolved_muele_map_dy_asimov_combine012tagQ.json plots resolved
~~~

To produce output for linearity tests, run the following. It is assumed, that truth asymmetry values are stored in `config/truth_dY.json`. One can specify path to a different json file by adding config option `-c path-to-json-truth-dY.json` to the `Pulls.py` script
~~~{.sh}
python python/Pulls.py -t '' -a 'A6neg A4neg A2neg A2pos A4pos A6pos' -i outputs/ -n asimov_combined_inclusive_110404 -s 110404
~~~


### Plotting pulls and constrains 
To plot the pulls and constrains of the individual parameters the script `python/make_brazilian.py` is provided.
Example usage:
~~~{.sh}
python python/make_brazilian.py --asimov_path path_to_asimov/outputFileNuis_seed-1map_dy_asimov_resolved_muelecombine12tagQ_boosted_muelecombine12tagQ.json --data_path path_to_data/outputFileNuis_seed-1map_dy_data_resolved_muelecombine12tagQ_boosted_muelecombine12tagQ.json --lumi '80.0 fb^{-1}' --outfile plot_Nuisances.pdf 
~~~

### Post-fit correlations for nuisance parameters
When running with nuisance parameters, it is possible to plot the post-fit correlation matrix of the nuisance parameters. For this the script `python/postFitCorr.py` is provided.
For it's usage run `python/postFitCorr.py -h`
Note, that this script requires a txt file with list of nuisance parameters one-per-line. An example file is provided in `config/examples/systematics_list.txt`
Example usage:
~~~{.sh}
python python/postFitCorr.py -l ./systematics_list.txt ./output -n 'path_to_nuisance_parameters_full_trace.npy'
~~~
where `./output` is the FBU-produced output directory with .npy files with sampling traces for each nuisance parameter. By default, a plot `correlations_postFit_NPs.pdf` will be produced in the same directory. To change the directory, use `-o` parameter, for different name of the file, use `-p` argument. In addition, *to get rid of insignificant correlations* and thus to reduce the size of the plot, it is possible to use parameter `-t <thresh>` option, where `<thres>` is a number from `0.` to `1.`, specifying a correlation threshold. Thus any nuisance parameter which is not correlated with any other nuisance parameter by at least the threshold value of correlation, is dropped from the plot.

In addition, it is also possible to show correlations between NPs and unfolded d|Y| bins and Ac itself (even for differential case, you will just have more parameters in the matrix) by specifying path to unfolded bin trace (`-b` option) and Ac trace respectively (`-a` option).

### Post-fit plots
Having the full unfolded trace for the truth and nuisance parameters, it is possible to create post-fit signal and background distributions, for the unfolded delta|y| and also for variables that are not unfolded (control plots). For this the script `python/createPostFitControlHistograms.py` is provided.
Example usage:
~~~{.sh}
python python/createPostFitControlHistograms.py -t 'betatt' -o 'outputs_betatt_data_profile_all_005_001' -a 'data' -p 'postFit' -d 'ljets' -g 'config/config_unfolding_dybetatt_005_001.json' -e 'resolved_muelecombine12tagQ_boosted_muelecombine12tagQ' -z '~/analyza/TopNtupleAnalysis_TCA/plotting/root_files' -f 'plotting_AT2_30_v6_all_combined_emu_' -x '_005_001'
~~~
where first argument is similar as for runUnfolding.py (empty - inclusive, pttt, mtt, betatt), `outputs` is the FBU-produced output directory with .npy files with sampling traces for each nuisance parameter. `data` has alternatives `asimov`, or protos reweighted, e.g. `A1pos`. `postFit` is the name of the output directory where the postFit histograms are saved in root files. `ljets` is the decay channel, `config/config_unfolding.json` is the config file with list of systematics, backgrounds, control histograms to process etc.  The `-e` specifies the channel combination used, `-z` is the path to plotting files, -f` is the prefix of the plotting root files and -x is the extra text used in the names of the output root files.

### Ranking of systematics effect on Ac
A natural question "How big of an impact on Ac does each systematic have" becomes less trivial when profiling is involved. A procedure as follows is used to estimate effect of individual uncertainties on Ac:

  * Prepare FBU inputs with full systematics, ommitting the systematic to be evaluated for its effect on Ac.
  * Use the investigated systematic's shift as the asimov pseudodata and unfold this shifted pseudodata
  * Compare unfolded Ac value to nominal

This procedure should give a reasonable estimate of the effect of a systematic uncertainty, while still considering all the constraints and pulls from other systematics on the final result.

**Usage:**

To produce the JSON inputs for all the systematics ranking, use `make_syst_rank_inputs.py`:
~~~{.sh}
python python/make_syst_rank_inputs.py -i data/json -o data/json_systrank -g config/examples/config_unfolding_example.json -e 'resolved_muelecombine12tagQ_boosted_muelecombine12tagQ' -v 'map_dypttt' -c 'outputFileNuis_whatever.json'
~~~
The script takes paths to input (`-i`) and output (`-o`) folders. Inputs should use the JSON format used bu `runUnfolding.py`. The output folder will be filled with directories for each systematic ranking, each of these folders containing the JSON inputs. parameter `-g`, `-e` and `-v` follow the parameters used in `runUnfolding.py`, to preserve the JSON format to be run by `runUnfolding.py` for each systematic ranking. See its examples above for its usage. The parameter `-c` is an **optional** parameter using which one can load nuisance parameters pulls&constraints JSON file which is normally produced by `runUnfolding.py`. This parameter changes the behavior of the syst ranking such that the pseudodata is not shifted by +/-1 sigma variation, but instead it is varied by the constrained variation, reading the constraints from the JSON file.

One can then run standard unfolding as shown in examples above using these JSON inputs. This task is suited for automated batch scripting, so we provide an example shell script to launch batch jobs `scripts/examples/submit_FBU_syst_ranking.sh`. Feel free to adapt the script to your own batch system -- internally we then use `submit_batch.py` script to submit many jobs to batch -- this script has support for qsub, bsub and sbatch (slurm) at the moment.

Since the systematics ranking is CPU intensitive (order of hundreds of full-syst unfoldings), it may become impractical to run on batch systems which could penalize this kind of heavy task by very low priority. See the section **Running FBU on grid** below for method of running these scripts on grid.

To plot a bar chart of the sorted systematics ranking, use:
~~~{.sh}
python python/make_syst_rank_summary.py -i output_syst_ranking_dy -o syst_rank_inclusive.pdf -g config/unfolding.json -p syst_rank_inclusive.txt
~~~
Explanation of parameters:

  * `-i` Specifies path to folder where the FBU ranking outputs are located. It is expected to contain folders named after individual systematic shifts and each of these folders should contain `Output.txt` from FBU that contains the array of Ac and Ac error for differential bins.
  * `-o` Path to pdf file into which the syst ranking plot will be made. The output file will have a `_binX` suffix, where `X=1..N` differential bins.
  * `-g` Path to JSON unfolding config. The config needs to contain the full list of systematics, two-sided, one-sided and normalization, in the standard format used by `runUnfolding.py`. The ranking script uses this information to correctly compare systematic shift to proper baseline (e.g. FS or AFII nominal, or 0th PDF variation, etc.)
  * `-p` (_Optional_) Path to text file where the syst ranking output will be written out. There will be output files with `_binX` suffix, where `X=1..N` differential bins.

Extra usefull parameter examples:
  * `-t` Show a line for total uncertainty -- Must have fullsyst asimov unfolding output in sub-folder `total` in the directory where all ranking output folders are present
  * `-q` Show a line for "naive sum of squared systematics" -- efffect of each systematic in ranking is summed in quadrature
  * `-s` Show a line for stat-only uncertainty

