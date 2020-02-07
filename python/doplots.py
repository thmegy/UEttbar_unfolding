import numpy as np
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import math
import pickle


def main(args):

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
        mean.append(np.mean(trace[i]))
        rms.append(np.std(trace[i])) 

        hist = plt.hist(trace[i], 50, label='posterior, rms = {0:.1f}'.format(np.std(trace[i])), alpha=0.7)
        mode = (hist[1][np.where(hist[0] == np.amax(hist[0]))[0][0]] + hist[1][np.where(hist[0] == np.amax(hist[0]))[0][0] + 1]) / 2

        plt.axvline(truth[i], color = 'red',linestyle='dashed', label='truth')
        plt.axvline(np.mean(trace[i]), color = 'green', label='mean = {0:.1f}'.format(np.mean(trace[i])))
        plt.axvline(mode, color = 'orange', label='mode = {0:.1f}'.format(mode))
    
        plt.legend()
        plt.xlabel('truth value')
        plt.ylabel('number of samples')
        plt.savefig(args.path+'plots/truthbin%i.eps'%int(i))
        plt.close()


    # Plot posterior of spin/polarisation parameter
    x = [-1. + (1./float(len(trace))) + i*2./float(len(trace)) for i in range(len(trace))]   # Get center of bins

    corr = -9 * np.sum(trace.transpose()*x, axis=1) / np.sum(trace.transpose(), axis=1)   # Compute correlation for each sample
    plt.hist(corr, 50, label='posterior, rms = {0:.3f}'.format(np.std(corr)), alpha=0.7)
    plt.axvline(np.mean(corr), color = 'green', label='mean = {0:.3f}'.format(np.mean(corr)))
    plt.legend()
    plt.xlabel('-9<{}>'.format(args.path.replace('/','')))
    plt.ylabel('number of samples')
    plt.savefig(args.path+'plots/'+args.path.replace('/','')+'.eps')
    plt.close()
    print( '{} = {} +- {}'.format(args.path.replace('/', ''), np.mean(corr), np.std(corr)) )

    # Alternative Computation of spin obsevable, from unfolded spectrum
    average = sum( [x[i] * mean[i] for i in range(len(mean))] ) / sum(mean)
    sum_bins_content = sum( mean )
    sum_bins_weighted = sum( [x[i] * mean[i] for i in range(len(mean))] )

    cov = np.cov(trace, bias = True)
    variance = 0.
    for i in range(len(trace)):
        for j in range(len(trace)):
            variance += ((x[i]*sum_bins_content + sum_bins_weighted) / sum_bins_content**2) * ((x[j]*sum_bins_content + sum_bins_weighted) / sum_bins_content**2) * cov[i][j]

    print( '{} = {} +- {}'.format(args.path.replace('/', ''), -9 * average, 9 * np.sqrt(variance)) )


    # Plot unfolded spectrum
    xerr = [1./float(len(truth)) for i in range(len(truth))]
    yerr = [0. for i in range(len(truth))]

    fig, ax = plt.subplots()
    ax.errorbar(x, truth, xerr=xerr, yerr=yerr, fmt='o', label='truth')
    ax.errorbar(x, mean, yerr=rms, fmt='o', label='unfolded')

    plt.ylabel('Number of events')
    plt.xlabel(args.path.replace('/', ''))
    plt.legend()
    #plt.tight_layout()
    ax.ticklabel_format(axis='y', style='sci', scilimits=(0,3))
    plt.text(0.5, 0.5, '-9<{0}> = {1:.3f} +- {2:.3f}'.format(args.path.replace('/', ''), -9 * average, 9 * np.sqrt(variance)), transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.savefig(args.path+'plots/unfolded.eps')
    plt.close()


    # Plot nuisance parameter pulls
    pulls = []

    with open (args.path+args.nptrace, 'rb') as f:
        nptrace = pickle.load(f)
        for syst, val in nptrace.items():
            pulls.append( (syst, np.mean(val), np.std(val)) )

            hist = plt.hist(val, 50, label='posterior, rms = {0:.1f}'.format(np.std(val)), alpha=0.7)
            mode = (hist[1][np.where(hist[0] == np.amax(hist[0]))[0][0]] + hist[1][np.where(hist[0] == np.amax(hist[0]))[0][0] + 1]) / 2
            
            plt.axvline(np.mean(val), color = 'green', label='mean = {0:.1f}'.format(np.mean(val)))
            plt.axvline(mode, color = 'orange', label='mode = {0:.1f}'.format(mode))
            
            plt.legend()
            plt.title(syst)
            plt.xlabel('Nuisance Parameter')
            plt.ylabel('number of samples')
            plt.savefig('{}plots/{}.eps'.format(args.path, syst))
            plt.close()
            

    fig, ax = plt.subplots()
    yticks = []
    yticks_label = []
    height = 1.
    for i, pull in enumerate(pulls):
        ax.errorbar(pull[1], i+1, xerr=pull[2], color='black', marker='o')
        yticks.append(i+1)
        yticks_label.append(pull[0].replace('weight_', ''))
        height += 1

    ax.axvline(0, color = 'black', linestyle=':')
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticks_label)
    ax.tick_params(axis='y', labelsize=8)

    mintwosig = patches.Rectangle((-2,0), 1, height, linewidth=1, edgecolor='yellow',facecolor='yellow')
    plustwosig = patches.Rectangle((1,0), 1, height, linewidth=1, edgecolor='yellow',facecolor='yellow')
    onesig = patches.Rectangle((-1,0), 2, height, linewidth=1, edgecolor='limegreen',facecolor='limegreen')
    ax.add_patch(mintwosig)
    ax.add_patch(plustwosig)
    ax.add_patch(onesig)

    plt.xlabel('Nuisance Parameter')
    plt.xlim(-2.25, 2.25)
    plt.tight_layout()
    plt.savefig('{}plots/pulls.eps'.format(args.path))








if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('path', type=str, help='path to inputs')
    parser.add_argument('--trace',  type=str, help='trace of bins', default='OutDir/trace.npy')
    parser.add_argument('--nptrace',  type=str, help='trace of nuisance parameters', default='OutDir/nptrace.pkl')
    parser.add_argument('--truth',  type=str, help='truth level spectrum', default='truth.json')

    args = parser.parse_args()
    main(args)
