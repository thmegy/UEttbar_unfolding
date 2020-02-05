import ROOT as r
from numpy import dot, random
import numpy as np
import json
from utils import writejson
import sys, os
import copy
#________________________________________
def getEff(resmat,htruth,y):
    nxx = htruth.GetNbinsX()
    xx = y%nxx
    if xx==0: xx=nxx
    yy = int((y-1)/nxx)+1
    if htruth.GetBinContent(xx,yy)==0. or resmat.Integral(0,-1,y,y)==0.:
        return 0.
    return resmat.Integral(0,-1,y,y)/htruth.GetBinContent(xx,yy)


#________________________________________
def histo2list(histo):
    nbinsx = histo.GetNbinsX()
    binlist = [histo.GetBinContent(x) for x in range(1,nbinsx+1)]
    print (histo.GetBinContent(-1),'  ',histo.GetBinContent(nbinsx+1))
    binlist[0]=binlist[0]+histo.GetBinContent(-1)
    binlist[-1]=binlist[-1]+histo.GetBinContent(nbinsx+1)

    return binlist


#________________________________________
def testinputs(truth,resmat,reco):
    myreco = dot(truth,resmat)
    assert(len(myreco)==len(reco)),'check resmat truth failed, not same dimension '
    for i in range(len(myreco)):
        if reco[i]==0.:print('reco bin={}  value={}'.format(i,reco[i]))
        if abs(1-myreco[i]/reco[i])>0.005:
            print ('----------------> bin={} failed with diff={}. dot={}   reco={}'.format(i, abs(1-myreco[i]/reco[i]),myreco[i], reco[i]))

#________________________________________
def gethisto(tfn,hname):
    tfo=None
    h=None

    try:
        tfo = r.TFile.Open(tfn)
    except IOError as e:
        print ('I/O error({0}): {1}').format(e.errno, e.strerror)
    except:
        print ('Unexpected error:'), sys.exc_info()[0]

    try:
        h = tfo.Get(hname)
        if h==None: 
            print ('the histogram={} does not exists'.format(hname))
            sys.exit(3)
    except IOError as e:
        print ('I/O error({0}): {1}'.format(e.errno, e.strerror))
    except:
        print ('Unexpected error:', sys.exc_info()[0])


    if h!=None:
        hclone=copy.deepcopy(h)
        tfo.Close()
        return hclone
    return h


#________________________________________
def getSystList(inputfile):
    systs = []
    try:
        infile = open(inputfile, 'r')
        lines = infile.readlines()
        for line in lines:
            if ('#' not in line) and (line is not '\n') :
                systs.append(line.replace('\n', ''))
    except:
        sys.exit('The systematics could not be recovered!!')

    return systs





#________________________________________
if(__name__=="__main__"):

    if len(sys.argv)!=3:
        sys.exit('usage: python python/makeresmat.py infile.root variable')

    tfn = sys.argv[1]
    hname_data   = 'mcdata'
    hname_truth  = 'ttbar_truth'
    hname_resmat = 'reco_vs_truth'
    hname_bkg   = ['singletop', 'diboson']
    systs = getSystList('python/systematics.txt')

    if '.root' not in tfn:
        sys.exit('input file is not a ROOT file')

    if  not os.path.isfile(tfn):
        sys.exit('inut file does not exist')
        
    h_data = gethisto(tfn,hname_data)
    h_truth = gethisto(tfn,hname_truth)
    h_bkg = [gethisto(tfn,i) for i in hname_bkg]
   
    l_data = histo2list(h_data)
    l_truth = histo2list(h_truth)
    bkg_dict = {}
    for i, j in zip(hname_bkg, h_bkg):
        bkg_dict[i] = histo2list(j)


    if not os.path.isdir(sys.argv[2]):
        os.mkdir(sys.argv[2])

    writejson(sys.argv[2]+'/data.json',l_data)
    writejson(sys.argv[2]+'/truth.json',l_truth)
    writejson(sys.argv[2]+'/bkg.json',bkg_dict)

    h_mig  = gethisto(tfn,hname_resmat)

    nbinsx = h_mig.GetNbinsX()
    nbinsy = h_mig.GetNbinsY()

    migration = []
    for y in range(1,nbinsy+1):
        truthbin = []
        norm = h_mig.Integral(0,-1,y,y)
        for x in range(1,nbinsx+1):
            value=0.
            if h_mig.GetBinContent(x,y) >0:
                value = h_mig.GetBinContent(x,y)/norm
            value = value*getEff(h_mig,h_truth,y)
            truthbin.append(value)
        migration.append(truthbin)

    writejson(sys.argv[2]+'/resmat.json',migration)
    testinputs(l_truth, migration, l_data)


    ## Get systematic variations

    # For signal
    h_ttbar = gethisto(tfn, 'ttbar')
    l_ttbar = np.array(histo2list(h_ttbar))
    ttbar_syst_dict = {}
    for syst in systs:
        h_syst = gethisto(tfn, 'ttbar_{}'.format(syst))
        l_syst = np.array(histo2list(h_syst))
        ttbar_syst_dict[syst] = (l_syst-l_ttbar) / l_ttbar

        writejson(sys.argv[2]+'/ttbar_syst.json', ttbar_syst_dict)


    ## For backgrounds
    bkg_syst_dict = {}
    for syst in systs:
        syst_dict = {}        
        for bkg in hname_bkg:
            h_bkg_syst = gethisto(tfn, '{}_{}'.format(bkg, syst))
            l_bkg_syst = np.array(histo2list(h_bkg_syst))
            syst_dict[bkg] = (l_bkg_syst-np.array(bkg_dict[bkg])) / np.array(bkg_dict[bkg])
        bkg_syst_dict[syst] = syst_dict

    writejson(sys.argv[2]+'/bkg_syst.json',bkg_syst_dict)
