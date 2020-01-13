from ROOT import TFile, TLorentzVector
from ROC import score_retrieval_std
import matplotlib.pyplot as plt
import numpy as np

def selection(event):
    keep = True
    if score_retrieval_std(event) < 0.99:
        keep = False
    vect = TLorentzVector()
    vect.SetPxPyPzE(event.GenJet[0],event.GenJet[1],event.GenJet[2],event.GenJet[3])
    if abs(vect.Eta())>0.5 or vect.Pt()<50 or vect.Pt()>70:
        keep = False
    vect.SetPxPyPzE(event.Jet[0],event.Jet[1],event.Jet[2],event.Jet[3])
    if abs(vect.Eta())>0.5 or vect.Pt()<50:
        keep = False

    return keep

def find_event_list(tree, selection):
    event_numbers = []
    for i, event in enumerate(tree):
        if selection(event):
            event_numbers.append(i)
    return event_numbers

def retrieve_ptcs(jet_dict):
    ptc_indexes = [i for i,node in enumerate(jet_dict['tree']) if all(node==[-1, -1])]
    possible_ids = [211,130,11,13,22]
    ptcs_dict = {}
    for pid in possible_ids:
        x = []
        y = []
        p = []
        ptcs_dict[pid] = [x,y,p]
    for index in ptc_indexes:
        pid = abs(jet_dict['content'][index][-1])
        ptcs_dict[pid][2].append(jet_dict['content'][index][0])
        ptcs_dict[pid][0].append(jet_dict['content'][index][1])
        ptcs_dict[pid][1].append(jet_dict['content'][index][2])
    return ptcs_dict
        

if __name__ == '__main__':
    workdir = '/data/gtouquet/testdir_23Sept'
    sfile = TFile(workdir+'/rawSignal.root')
    bfile = TFile(workdir+'/rawBackground.root')
    stree = sfile.Get('finaltree')
    btree = bfile.Get('finaltree')

    signal = True

    X,y = np.load('/data/gtouquet/testdir_23Sept/preprocessed_test_signal_anti-kt.npy') if signal else np.load('/data/gtouquet/testdir_23Sept/preprocessed_test_background_anti-kt.npy')
    tree = stree if signal else btree
    event_numbers = find_event_list(tree, selection)

    colordict = {211:'red',
                 130:'yellow',
                 11:'blue',
                 13:'green',
                 22:'brown'}
    
    # i=0
    # def onclick(event):
    #     global i
    #     i+=1
    #     event_index = event_numbers[i]
    #     ptcs_dict = retrieve_ptcs(X[event_index])
    #     ax.clear()
    #     for pid, ptclist in ptcs_dict.iteritems():
    #         ax.scatter(ptclist[0],ptclist[1], s=ptclist[2]*1000, c=colordict[pid], label=pid)
    #     ax.legend()
    #     plt.show()
    #     # print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
    #     #       ('double' if event.dblclick else 'single', event.button,
    #     #        event.x, event.y, event.xdata, event.ydata))

    # cid = fig.canvas.mpl_connect('button_press_event', onclick)
    for event_index in event_numbers:
        fig, ax = plt.subplots()
        ptcs_dict = retrieve_ptcs(X[event_index])
        for pid, ptclist in ptcs_dict.iteritems():
            ax.scatter(ptclist[0],ptclist[1], s=[x*10 for x in ptclist[2]], c=colordict[pid], label=pid, alpha = 0.5)
        ax.legend()
        print 'before plot'
        plt.show()
        print 'after plot'
