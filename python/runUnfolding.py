import fbu
import json
import numpy as np

def formattrace(trace):
    tmp = [bins for bins in zip(*trace)]
    return tmp

def default(o):
    if isinstance(o, np.int64): return int(o)
    elif isinstance(o, np.float32): return float(o)
    raise TypeError

defaultOptions = {
    'prior' : 'Uniform',
    'nCores' : 4,
    'nChains' : 4,
    'monitoring' : False,
    'verbose' : False,
    'discard_tuned_samples' : True
}

myfbu = fbu.PyFBU()
myfbu.prior = defaultOptions['prior']
myfbu.nCores = defaultOptions['nCores']
myfbu.nChains = defaultOptions['nChains']
myfbu.nMCMC = 10000
myfbu.nTune = int(myfbu.nMCMC/4)
myfbu.discard_tuned_samples = defaultOptions['discard_tuned_samples']
myfbu.nuts_kwargs={'target_accept':0.95}
myfbu.response   = json.load(open('resmat.json'))

myfbu.monitoring = defaultOptions['monitoring']
myfbu.verbose =defaultOptions['verbose']
myfbu.sampling_progressbar = True

truth = json.load(open('full.json'))

myfbu.lower = [abs(i*0.) for i in truth]
myfbu.upper = [abs(i*2.) for i in truth]

myfbu.rndseed == -1
myfbu.data = np.array(json.load(open('reco.json')))

myfbu.name = 'OutDir/'
print('Running FBU...')
myfbu.run()
trace = myfbu.trace

np.save('OutDir/fulltrace',trace)

with open('OutDir/'+'fulltrace.json','w') as outf:
    json.dump(formattrace(trace),outf, default=default)



