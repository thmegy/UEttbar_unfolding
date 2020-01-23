#!/bin/bash

shopt -s expand_aliases
if [[ -z ${ATLAS_LOCAL_ROOT_BASE+x} ]] ; then
  export ATLAS_LOCAL_ROOT_BASE='/cvmfs/atlas.cern.ch/repo/ATLASLocalRootBase'
fi
alias setupATLAS="source ${ATLAS_LOCAL_ROOT_BASE}/user/atlasLocalSetup.sh"

export LCG_ARCH=`head -n1 architecture.txt`

# in case running on RHEL/CENTOS/SLC 7
if echo "${LCG_ARCH}" | grep -Ei '(slc|centos)7' > /dev/null ; then
    if [[ -f '/opt/rh/devtoolset-7/enable' ]] ; then
        echo 'Activating RHEL7 compatibility'
        source /opt/rh/devtoolset-7/enable
    fi
fi

echo "> setupATLAS"
setupATLAS --quiet
echo "> Setup Python3+ROOT"
lsetup "lcgenv -p LCG_96python3rc1 ${LCG_ARCH} ROOT" --quiet
export UNFOLDINGDIR=$PWD
export OMP_NUM_THREADS=1 # if openblas is mltithreaded,it iterferes with our multithreaded FBU (especially if limited number of CPUs is specified on grid/batch), resulting in much slower performance

echo "> Loading virtualenv 'fbuenv'"
source fbuenv/bin/activate
