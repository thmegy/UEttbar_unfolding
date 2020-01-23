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
source install.sh x86_64-centos7-gcc8-opt
~~~
Where `x86_64-slc6-gcc62-opt` is the architecture of the system where you are setting things up. The example given works for lxplus, check your architecture (in particular `slc6` vs `slc5`, `centos7`, etc...) for use elsewhere. The `gcc` version is set to `gcc62` which is currently heavily used in recent ASG software releases and also supported by `lcg` software.

## Sourcing FBU environment

Once the install has been done, and each time when login to a new machine, use the `init.sh` script instead of above installation. 
Please note that it assumes that $ATLAS_LOCAL_ROOT_BASE variable is set up:
~~~{.sh}
source init.sh
~~~

# Examples for running FBU

## Preparing JSON inputs for FBU
FBU uses inputs in a `json` format. It is then necessary to transform histograms stored in ROOT files to `json` files.
In the following example, we copy a test file:
~~~{.sh}
cp /afs/cern.ch/user/h/helsens/public/UEttbar/ttbar_templates.root .
~~~

then we can produce `json` files 

~~~{.sh}
python python/makeresmat.py ttbar_templates.root ttbar_ntracks_asym2
~~~

One the files are produced, unfolding can be performed

~~~{.sh}
python python/runUnfolding.py --resmat resmat.json --reco reco.json --truth full.json
~~~

and plots can be made using the output produced
~~~{.sh}
python python/doplots.py OutDir/fulltrace.npy full.json
~~~
