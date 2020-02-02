import numpy as np
import json
import matplotlib.pyplot as plt
import os
import math

if(__name__=="__main__"):

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument( '-p', '--path', type=str, help='path to inputs')
    parser.add_argument('--trace',  type=str, help='trace of fbu', default='OutDir/fulltrace.npy')
    parser.add_argument('--truth',  type=str, help='truth level spectrum', default='truth.json')

    args, _ = parser.parse_known_args()

    trace=None
    try:
        trace = np.load(args.path + args.trace)
    except IOError as e:
        print ('I/O error({0}): {1}'.format(e.errno, e.strerror))
    
    truth = None
    with open(args.path + args.truth) as json_file:  
        try:
            truth = json.load(json_file)
        except ValueError as e:
            print ('ValueError error({0}): {1}'.format(e.errno, e.strerror))

    mean = []
    rms  = []
    if not os.path.isdir(args.path+'plots/'):
        os.mkdir(args.path+'plots/')


    for i in range(0, len(trace)):
        plt.hist(trace[i], 50, label='posterior', alpha=0.7)
        plt.axvline(truth[i], color = 'red',linestyle='dashed', label='truth')
        plt.axvline(np.mean(trace[i]), color = 'green', label='mean')
    
        mean.append(np.mean(trace[i]))
        rms.append(np.std(trace[i])) 

        plt.legend()
        plt.xlabel('truth value')
        plt.ylabel('number of samples')
        plt.savefig(args.path+'plots/truthbin%i.eps'%int(i))
        plt.close()


    #x = [2.5, 7.5, 12.5, 17.5, 22.5, 27.5, 35., 45., 60, 85]
    #xerr = [2.5, 2.5, 2.5, 2.5, 2.5, 2.5, 5, 5 ,10, 15]
    #yerr = [0,0,0,0,0,0,0,0,0,0]

    x = [-1. + (1./float(len(truth))) + i*2./float(len(truth)) for i in range(len(truth))]
    xerr = [1./float(len(truth)) for i in range(len(truth))]
    yerr = [0. for i in range(len(truth))]

    fig, ax = plt.subplots()
    ax.errorbar(x, truth, xerr=xerr, yerr=yerr, fmt='o', label='truth')
    ax.errorbar(x, mean, yerr=rms, fmt='o', label='unfolded')

    #plt.plot(truth, label='truth')
    plt.ylabel('Number of events')
    plt.xlabel(args.path.replace('/', ''))
    plt.legend()
    
    plt.savefig(args.path+'plots/unfolded.eps')
    plt.close()



    average = sum( [x[i] * mean[i] for i in range(len(mean))] ) / sum(mean)

    sum_bins_content = sum( mean )
    sum_bins_weighted = sum( [x[i] * mean[i] for i in range(len(mean))] )
    average_unc = math.sqrt( sum( [((x[i]*sum_bins_content + sum_bins_weighted) * rms[i])**2 for i in range(len(mean))] ) ) / sum(mean)**2

    print( '{} = {} +- {}'.format(args.path.replace('/', ''), -9 * average, 9 * average_unc) )
