"""
Preprocessing our files to a usable format for the recnn program.

input format :
	[ [[ p1, p2, p3, ... ]] , [[ p1, p2, p3, ... ]] , [[ p1, p2, p3, ... ]] , ...]
	pi = [E,px,py,pz,id ...]
	with "fake particles", i.e. pi=[0.,0.,0.,0.,...]
output format :
	[ [ p1, p2, ... ] , ...]
	pi = [E,px,py,pz,id=0]
	without fake particles
"""

import numpy as np
from ROOT import TFile, TLorentzVector, TH1F
import uproot
from recnn.preprocessing import multithreadmap



#now useless
def extract_first_element(jet):
	"""
	extract first element of the jet : its components.
	"""
	return(jet[0])


def find_first_non_particle(jet):
	"""
	dichotomy search of first  non particle of the jet
	"""
	n=len(jet)
	found = False
	first = 0
	last = n-1
	while not found and first <= last :
		m = (last+first)//2
		if jet[m][0] == 0. and jet[m-1][0] != 0. :
			found = True
		elif jet[m][0] != 0. :
			first = m+1
		else :
			last = m-1
	return(m)

def select_particle_features(jet, addID=False):
	"""
	select E,px,py,pz of the particle.
	"""
        if addID:
	        return(jet[:,[3,0,1,2,4,5,6,7]])
        else:
                return(jet[:,[3,0,1,2]])


def etatrimtree(tree, isSignal=False, JEC=False, cutfunc=None, norm_hist=None, background_norm_hist=None):
        newtree = tree.CloneTree(0)
        testtree = tree.CloneTree(0)
        genpt = np.zeros(1)
        testtree.Branch('genpt', genpt, 'genpt/D')
        newtree.Branch('genpt', genpt, 'genpt/D')
        geneta = np.zeros(1)
        testtree.Branch('geneta', geneta, 'geneta/D')
        newtree.Branch('geneta', geneta, 'geneta/D')
        genphi = np.zeros(1)
        testtree.Branch('genphi', genphi, 'genphi/D')
        newtree.Branch('genphi', genphi, 'genphi/D')
        rawpt = np.zeros(1)
        testtree.Branch('rawpt', rawpt, 'rawpt/D')
        newtree.Branch('rawpt', rawpt, 'rawpt/D')
        raweta = np.zeros(1)
        testtree.Branch('raweta', raweta, 'raweta/D')
        newtree.Branch('raweta', raweta, 'raweta/D')
        rawphi = np.zeros(1)
        testtree.Branch('rawphi', rawphi, 'rawphi/D')
        newtree.Branch('rawphi', rawphi, 'rawphi/D')
        recopt = np.zeros(1)
        testtree.Branch('recopt', recopt, 'recopt/D')
        newtree.Branch('recopt', recopt, 'recopt/D')
        recoeta = np.zeros(1)
        testtree.Branch('recoeta', recoeta, 'recoeta/D')
        newtree.Branch('recoeta', recoeta, 'recoeta/D')
        recophi = np.zeros(1)
        testtree.Branch('recophi', recophi, 'recophi/D')
        newtree.Branch('recophi', recophi, 'recophi/D')
        i=0
        j=0
        nentries = tree.GetEntries()
        for event in tree:
                j+=1
                if j%10000==0:
                    print 'entry', j, '/', nentries
                if event.dRs[4] > 0.1:
                        continue
                is_Signal = (event.dRs[0] < 0.3 and event.dRs[0]!=0.)
                if isSignal:
                        if not is_Signal:
                                continue
                else:
                        if is_Signal:
                                continue
                vect = TLorentzVector()
                vect.SetPxPyPzE(event.GenJet[0],event.GenJet[1],event.GenJet[2],event.GenJet[3])
                genpt[0] = vect.Pt()
                geneta[0] = vect.Eta()
                genphi[0] = vect.Phi()
                vect.SetPxPyPzE(event.RawJet[0],event.RawJet[1],event.RawJet[2],event.RawJet[3])
                rawpt[0] = vect.Pt()
                raweta[0] = vect.Eta()
                rawphi[0] = vect.Phi()
                vect.SetPxPyPzE(event.Jet[0],event.Jet[1],event.Jet[2],event.Jet[3])
                recopt[0] = vect.Pt()
                recoeta[0] = vect.Eta()
                recophi[0] = vect.Phi()
                if i%2==0:
                        testtree.Fill()
                else:
                        if not cutfunc and not cutfunc(event):
                                continue
                        if isSignal and not JEC:
                                vect.SetPxPyPzE(event.GenJet[0],event.GenJet[1],event.GenJet[2],event.GenJet[3])
                                norm_hist.Fill(vect.Pt())
                        if not isSignal and not JEC:
                                vect.SetPxPyPzE(event.GenJet[0],event.GenJet[1],event.GenJet[2],event.GenJet[3])
                                the_bin = norm_hist.FindBin(vect.Pt())
                                nsig = norm_hist.GetBinContent(the_bin)
                                nback = background_norm_hist.GetBinContent(the_bin)
                                if nback>=nsig:
                                        continue
                                else:
                                        background_norm_hist.Fill(vect.Pt())
                        newtree.Fill()
                i+=1
        newtree.SetName('traintree')
        testtree.SetName('testtree')
        newtree.Write()
        testtree.Write()
        return newtree, testtree
        
def cleanarray(jets_array, addID=False):
    indexes = multithreadmap(find_first_non_particle, jets_array)
    jets_array = list(jets_array)
    for i in range(len(jets_array)):
        jets_array[i] = jets_array[i][:indexes[i]]

        
    jets_array = multithreadmap(select_particle_features,jets_array, addID=addID)
    
    return jets_array
    
        
def converttorecnnfiles(inputfile, treename, addID=False, JEC=False, gen=False):
        tree = uproot.open(inputfile)[treename]
        branchname = 'genptcs' if gen else 'ptcs'
        if JEC:
            jets_array = tree.arrays(branchname)[branchname]
            genpt_array = tree.arrays('genpt')['genpt']
        else:
            jets_array = tree.arrays(branchname)[branchname]
        #process
        jets_array = cleanarray(jets_array, addID=addID)
        if JEC:
            genpt_array = list(genpt_array)
            jets_array = zip(jets_array, genpt_array)
        
        return jets_array

def makerecnnfiles_classification(rootfile_signal, rootfile_background, traincut):
        norm_hist = TH1F('normhist','normhist',150,0.,150.)
        background_norm_hist = TH1F('backgroundnormhist','backgroundnormhist',150,0.,150.)
        signal_file = TFile(rootfile_signal,'update')
        signal_tree = signal_file.Get('tree')
        stree, stesttree = etatrimtree(signal_tree, isSignal=True, JEC=False,cutfunc=traincut,norm_hist=norm_hist, background_norm_hist=background_norm_hist)
        signal_file.Close()
        train_array_signal = converttorecnnfiles(rootfile_signal, 'traintree', addID=True, JEC=False)
        test_array_signal = converttorecnnfiles(rootfile_signal, 'testtree', addID=True, JEC=False)
        background_file = TFile(rootfile_background,'update')
        background_tree = background_file.Get('tree')
        btree, btesttree = etatrimtree(background_tree, isSignal=False, JEC=False,cutfunc=traincut,norm_hist=norm_hist, background_norm_hist=background_norm_hist)
        background_file.Close()
        train_array_background = converttorecnnfiles(rootfile_background, 'traintree', addID=True, JEC=False)
        test_array_background = converttorecnnfiles(rootfile_background, 'testtree', addID=True, JEC=False)
        return train_array_signal, test_array_signal, train_array_background, test_array_background


# if __name__ == '__main__':
#         import argparse
#         parser = argparse.ArgumentParser(description='Convert Dataformated ROOTfiles to numpy files usable in the notebooks. \n Usage : \n python converttorecnnfiles.py /data/gtouquet/samples_root/QCD_Pt80to120_ext2_dataformat.root --isSignal False \n OR \n python converttorecnnfiles.py all')
#         parser.add_argument("--rootfile", help="path to the ROOTfile to be converted OR 'all' which converts all usual datasets from gael's directory (for now, maybe put the rootfiles in data/ too?)",type=str, default='all')
#         parser.add_argument("--isSignal", help=" if is it a signal file (hadronic taus) or background file (QCD jets)?", action="store_true")
#         parser.add_argument("--addID", help="whether or not to add the pdgID in the output", action="store_true")
#         parser.add_argument("--JEC", help="to make the files needed for JEC regression", action="store_true")
#         parser.add_argument("--tag", help="what tag to add to name of output files", type=str, default='')
#         parser.add_argument("--etacut", help="what eta cut to require", type=float, default=2.3)
#         parser.add_argument("--ptmin", help="what ptmin cut to require", type=float, default=20.)
#         parser.add_argument("--ptmax", help="what ptmax cut to require", type=float, default=100.)
#         args = parser.parse_args()
#         if args.tag != '':
#             args.tag = '_'+args.tag
#         idtag = ''
#         if args.addID:
#             idtag = '_ID'
        

#         if args.rootfile == 'all':
#                 if not args.JEC:
#                     #Signal files
#                     sinputfile = TFile('/data/gtouquet/samples_root/RawSignal.root')
#                     stree = sinputfile.Get('tree')
#                     outROOTfiles = TFile('/data/gtouquet/samples_root/Test_Train_splitted_{}.root'.format('Signal'),'recreate')
#                     #load data
#                     tree, testtree = etatrimtree(stree, isSignal=True, JEC=args.JEC)
#                     signals, testsignals = converttorecnnfiles(stree,
#                                                                addID=args.addID,
#                                                                isSignal=True,
#                                                                JEC=args.JEC,
#                                                                etacut=args.etacut,
#                                                                ptmin=args.ptmin,
#                                                                ptmax=args.ptmax)
#                     outROOTfiles.Write()
#                     outROOTfiles.Close()
#                     np.save('data/{}{}{}{}'.format('Signal', '_JEC' if args.JEC else '','_train', idtag, args.tag), signals)
#                     np.save('data/{}{}{}{}'.format('Signal', '_JEC' if args.JEC else '','_test', idtag, args.tag), testsignals)
                    
#                 #Background files
#                 binputfile = TFile('/data/gtouquet/samples_root/RawBackground_17july.root')
#                 btree = binputfile.Get('tree')
#                 outROOTfileb = TFile('/data/gtouquet/samples_root/Test_Train_splitted_{}{}.root'.format('Background','_JEC' if args.JEC else ''),'recreate')
#                 backgrounds, testbackgrounds = converttorecnnfiles(btree,
#                                                                    addID=args.addID,
#                                                                    isSignal=False,
#                                                                    JEC=args.JEC,
#                                                                    etacut=args.etacut,
#                                                                    ptmin=args.ptmin,
#                                                                    ptmax=args.ptmax)
#                 outROOTfileb.Write()
#                 outROOTfileb.Close()
#                 np.save('data/{}{}{}{}'.format('Background', '_JEC' if args.JEC else '','_train', idtag,'_'+args.tag), backgrounds)
#                 np.save('data/{}{}{}{}'.format('Background', '_JEC' if args.JEC else '','_test', idtag,'_'+args.tag), testbackgrounds)
                
                
#         else:
#                 inputfile = TFile(args.rootfile)
#                 tree = inputfile.Get('tree')
#                 converttorecnnfiles(tree,
#                                     addID=args.addID,
#                                     isSignal=args.isSignal,
#                                     JEC=args.JEC,
#                                     etacut=args.etacut,
#                                     ptmin=args.ptmin,
#                                     ptmax=args.ptmax)
