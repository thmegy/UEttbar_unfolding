import fbu
import json
import numpy as np
import os

defaultOptions = {
    'prior' : 'Uniform',
    'priorparams' : {},
    'nCores' : 4,
    'nChains' : 4,
    'monitoring' : False,
    'verbose' : False,
    'discard_tuned_samples' : True
}

def formattrace(trace):
    tmp = [bins for bins in zip(*trace)]
    return tmp

def default(o):
    if isinstance(o, np.int64): return int(o)
    elif isinstance(o, np.float32): return float(o)
    raise TypeError

#________________________________________
if(__name__=="__main__"):

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument( '-p', '--path', type=str, help='path to inputs')
    parser.add_argument('--truth',  type=str, help='truth spectrun in json file', default='truth.json')
    parser.add_argument('--data',   type=str, help='data spectrum in json file', default='data.json')
    parser.add_argument('--bkg',   type=str, help='background spectrum in json file', default='bkg.json')
    parser.add_argument('--resmat', type=str, help='response matrix in json file', default='resmat.json')
    parser.add_argument('--outdir', type=str, help='out directory to store outputs', default='OutDir')

    args, _ = parser.parse_known_args()
    truth = args.path + args.truth
    data  = args.path + args.data
    bkg  = args.path + args.bkg
    resmat = args.path + args.resmat
    outdir = args.path + args.outdir

    myfbu = fbu.PyFBU()
    myfbu.prior = defaultOptions['prior']
    myfbu.nCores = defaultOptions['nCores']
    myfbu.nChains = defaultOptions['nChains']
    myfbu.nMCMC = 10000
    myfbu.nTune = int(myfbu.nMCMC/4)
    myfbu.discard_tuned_samples = defaultOptions['discard_tuned_samples']
    myfbu.nuts_kwargs={'target_accept':0.95}
    myfbu.response   = json.load(open(resmat))

    myfbu.monitoring = defaultOptions['monitoring']
    myfbu.verbose =defaultOptions['verbose']
    myfbu.sampling_progressbar = True

    truth = json.load(open(truth))

    myfbu.lower = [abs(i*0.) for i in truth]
    myfbu.upper = [abs(i*10.) for i in truth]
    myfbu.priorparams = defaultOptions['priorparams']


    bkgs = json.load(open(bkg))
    myfbu.background = {}
    myfbu.backgroundsyst = {}
    for bkg in bkgs:
        myfbu.background[bkg[0]] = bkg[1]
        myfbu.backgroundsyst[bkg[0]] = 0.

    myfbu.rndseed == -1
    myfbu.data = np.array(json.load(open(data)))

    myfbu.name = outdir
    if not os.path.exists(myfbu.name):
        os.makedirs(myfbu.name)
    print('Running FBU...')
    myfbu.run()
    trace = myfbu.trace

    np.save(outdir+'/fulltrace',trace)

    with open(outdir+'/'+'fulltrace.json','w') as outf:
        json.dump(formattrace(trace),outf, default=default)



