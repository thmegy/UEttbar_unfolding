import ROOT as r
from numpy import dot, random
import json
from utils import writejson

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
        if abs(1-myreco[i]/reco[i])>0.0000005:
            print ('----------------> bin={} failed with diff={}. dot={}   reco={}'.format(i, abs(1-myreco[i]/reco[i]),myreco[i], reco[i]))

#________________________________________
if(__name__=="__main__"):

    tfo = r.TFile.Open('/afs/cern.ch/user/h/helsens/public/UEttbar/ttbar_templates.root')

    h_reco = tfo.Get('ttbar_ntracks_asym2_reco')
    l_reco = histo2list(h_reco)

    h_full = tfo.Get('ttbar_ntracks_asym2_truth')
    l_full = histo2list(h_full)

    writejson('reco.json',l_reco)
    writejson('full.json',l_full)

    h_mig  = tfo.Get('ttbar_2d_ntracks_asym2_reco_vs_truth')

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
            value = value*getEff(h_mig,h_full,y)
            truthbin.append(value)
        migration.append(truthbin)

    writejson('resmat.json',migration)
    testinputs(l_full, migration, l_reco)

