import numpy as np
import json
import matplotlib.pyplot as plt
import sys

if len(sys.argv)!=3:
    sys.exit('usage: python python/doplots.py trace.npy truth.json')

trace=None
try:
    trace = np.load(sys.argv[1])
except IOError as e:
    print ('I/O error({0}): {1}'.format(e.errno, e.strerror))
    
truth = None
with open(sys.argv[2]) as json_file:  
    try:
        truth = json.load(json_file)
    except ValueError as e:
        print ('ValueError error({0}): {1}'.format(e.errno, e.strerror))

mean = []
rms  = []

for i in range(0, len(trace)):
    plt.hist(trace[i], 50, label='posterior', alpha=0.7)
    plt.axvline(truth[i], color = 'red',linestyle='dashed', label='truth')
    plt.axvline(np.mean(trace[i]), color = 'green', label='mean')
    
    mean.append(np.mean(trace[i]))
    rms.append(np.std(trace[i])) 

    plt.legend()
    plt.xlabel('truth value')
    plt.ylabel('number of samples')
    plt.savefig('truthbin%i.eps'%int(i))
    plt.close()


#x = [2.5, 7.5, 12.5, 17.5, 22.5, 27.5, 35., 45., 60, 85]
#xerr = [2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 5, 5 ,10, 15]
#yerr = [0,0,0,0,0,0,0,0,0,0]

x = [-0.875,-0.625,-0.375,-0.125,0.125,0.375,0.625,0.875]
xerr = [0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25]
yerr = [0,0,0,0,0,0,0,0]

fig, ax = plt.subplots()
ax.errorbar(x, truth, xerr=xerr, yerr=yerr, fmt='o', label='truth')
ax.errorbar(x, mean, yerr=rms, fmt='o', label='unfolded')

#plt.plot(truth, label='truth')
plt.ylabel('Number of events')
plt.xlabel('CorrKK')
plt.legend()

plt.savefig('unfolded.eps')
plt.close()
