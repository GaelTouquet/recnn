import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from ROOT import TFile, TLorentzVector
from root_to_npy import cleanarray
import uproot

def plot_jet(jet, genjet, title=''):
    energies = jet[:,0]
    pxs = jet[:,1]
    pys = jet[:,2]
    pzs = jet[:,3]
    ids = jet[:,4]
    ps = np.sqrt(pxs*pxs + pys*pys + pzs*pzs)
    etas = 0.5 * (np.log(ps + pzs) - np.log(ps - pzs))
    phis = np.arctan2(pys, pxs)
    pts = ps / np.cosh(etas)
    
    color_dict = {211:"black",
                  130:"red",
                  11:"blue",
                  13:"green",
                  22:"yellow",
                  'other':"magenta"}
    colors = [color_dict[abs(i)] for i in ids]
    color_handles = []
    for pdgid, color in color_dict.iteritems():
        color_handles.append(mpatches.Patch(color=color,label=str(pdgid)))


    genenergies = genjet[:,0]
    genpxs = genjet[:,1]
    genpys = genjet[:,2]
    genpzs = genjet[:,3]
    genids = genjet[:,4]
    genps = np.sqrt(genpxs*genpxs + genpys*genpys + genpzs*genpzs)
    genetas = 0.5 * (np.log(genps + genpzs) - np.log(genps - genpzs))
    genphis = np.arctan2(genpys, genpxs)
    genpts = genps / np.cosh(genetas)
    
    color_dict = {211:"black",
                  130:"red",
                  11:"blue",
                  13:"green",
                  22:"yellow",
                  321:"black",
                  310:"red",
                  2112:"red",
                  3334:"black",
                  'other':"magenta"
                  }
    gencolors = []
    for i in genids:
        if abs(i) in color_dict:
            gencolors.append(color_dict[abs(i)])
        else:
            print i, 'not in dict'
            gencolors.append(color_dict['other'])
    plt.rc('text, usetex=True')
    plt.rc('font', family='serif')
    figure = plt.figure(figsize= (10,20))
    ax = figure.add_subplot(1,2,1)
    scatter = ax.scatter(etas,phis,s=10*pts,c=colors,alpha=0.8)
    # handles, labels = scatter.legend_elements()
    # import pdb;pdb.set_trace()
    # idlegend = ax.legend(handles=color_handles,
    #                      loc="upper right", title="pdgId", bbox_to_anchor=(1.125,1.1),framealpha=1.)
    ax.set_ylabel(r'$\phi$')
    ax.set_xlabel(r'$\eta$')
    ax.set_title('Reconstructed particles')
    ax.set_ylim([-0.75,0.25])
    ax.set_xlim([-0.75,0.25])
    
    ax = figure.add_subplot(1,2,2)

    scatter = ax.scatter(genetas,genphis,s=10*genpts,c=gencolors,alpha=0.8)
    ax.set_title('Gen level particles')
    ax.set_ylabel(r'$\phi$')
    ax.set_xlabel(r'$\eta$')
    ax.set_ylim([-0.75,0.25])
    ax.set_xlim([-0.75,0.25])
    
    
    plt.show()


# def make_selecttree(tfile, selection):
#     scores = []
#     f = TFile(tfile)
#     tree = f.Get('finaltree')
#     fout = TFile('tmp.root','recreate')
#     newtree = tree.CloneTree(0,'SortBasketsByBranch')
#     newtree.SetName('selecttree')
#     for i,event in enumerate(tree):
#         tree.GetEntry(i)
#         if selection(event):
#             scores.append([score_retrieval_NN(event),score_retrieval_std(event)])
#             newtree.Fill()
#     newtree.Write()
#     fout.Close()
#     f.Close()
#     return scores
    

# def my_selection(event, good_std=False, signal=False):
#     vect = TLorentzVector()
#     vect.SetPxPyPzE(event.GenJet[0],event.GenJet[1],event.GenJet[2],event.GenJet[3])
#     if abs(vect.Eta())>0.5 or vect.Pt()<50 or vect.Pt()>70:
#         return False
#     vect.SetPxPyPzE(event.Jet[0],event.Jet[1],event.Jet[2],event.Jet[3])
#     if abs(vect.Eta())>0.5 or vect.Pt()<50:
#         return False
#     NN_score = score_retrieval_NN(event)
#     if signal:
#         is_bad_identified = NN_score < 0.1
#     else:
#         is_bad_identified = NN_score > 0.9
#     if good_std:
#         std_score = score_retrieval_std(event)
#         if signal:
#             is_std_good = std_score > 0.9
#         else:
#             is_std_good = std_score < 0.1

#     keep = is_bad_identified

#     if good_std:
#         keep = keep and is_std_good

        
#     return keep

plot_signal = False
good_std = True
skip_missing_genptcs = True

if plot_signal:
    rootfilename = '/data2/gtouquet/RECNNDIR_tests_190521/rawSignal.root'
    title = 'tau \n RecNN score : {}'
    if good_std:
        title = 'tau \n RecNN score : {} ; std score : {}'
    sel = lambda event : my_selection(event, good_std, signal=True)
else:
    rootfilename = '/data2/gtouquet/RECNNDIR_tests_190521/rawBackground.root'
    title = 'QCD jet \n RecNN score : {}'
    if good_std:
        title = 'QCD jet \n RecNN score : {} ; std score : {}'
    sel = lambda event : my_selection(event, good_std, signal=False)
    
# scores = make_selecttree(rootfilename, sel)
# print 'tree selected'

tree = uproot.open(rootfilename)['finaltree']
arrays = tree.arrays(['ptcs','genptcs','geneta','genpt','recopt','recoeta','standardID','antikt','isSignal'])

jets_array = cleanarray(arrays['ptcs'],addID=True)
genjets_array = cleanarray(arrays['genptcs'],addID=True)

# jets_array = converttorecnnfiles('tmp.root', 'selecttree', addID=True, JEC=False)
# genjets_array = converttorecnnfiles('tmp.root', 'selecttree', addID=True, JEC=False, gen=True)

# njets = len(jets_array)

for i,jet in enumerate(jets_array):
    if (abs(arrays['geneta'][i]) >0.5 or abs(arrays['recoeta'][i]) >0.5 or arrays['genpt'][i] <50. or arrays['genpt'][i] >70. or arrays['recopt'][i] < 50.):
        continue

    if len(genjets_array[i])==0:
        print 'missing genptcs'
        if skip_missing_genptcs:
            continue
    score_NN = arrays['antikt'][i]

    iso_score = arrays['standardID'][i][0]
    if iso_score != 0.:
        iso_score += 1
        iso_score /= 2
        
    decaymode_finding = arrays['standardID'][i][1] > 0.5
    if not decaymode_finding:
        iso_score *= 0.
            
    dz = abs(arrays['standardID'][i][2]) < 0.2
    if not dz:
        iso_score *= 0.

    score_std = iso_score
        
    if plot_signal:
        if good_std:
            if score_std < 0.7:
                continue
        if score_NN > 0.3:
            continue
    else:
        if good_std:
            if score_std > 0.3:
                continue
        if score_NN < 0.7:
            continue
            
    this_title = title.format(str(score_NN)[:6],str(score_std)[:6])
    plot_jet(jet, genjets_array[i], this_title)
