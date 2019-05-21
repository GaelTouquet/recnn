from ROOT import TFile, TH2F, TGraph, TLegend, TCanvas
import numpy as np
from tdrstyle import setTDRStyle
setTDRStyle(square=False)

f = TFile('/data/gtouquet/testdir_23Sept/ROCs.root')
tree = f.Get('NN_ROC')
stdtree = f.Get('std_ROC')

basegraph = TH2F('basegraph','#tau_{h} ID ROC curve',10,0.001,1.,10,0.,1.)
basegraph.SetStats(0)
basegraph.GetXaxis().SetTitle('Jet #rightarrow #tau_{h} fake misidentification rate')
basegraph.GetXaxis().SetTitleSize(.05)
basegraph.GetXaxis().SetTitleOffset(1.2)
basegraph.GetYaxis().SetTitle('#tau_{h} identification efficiency')
basegraph.GetYaxis().SetTitleSize(.05)


tpr = np.zeros(stdtree.GetEntries())
fpr = np.zeros(stdtree.GetEntries())
i = 0
for event in stdtree:
    tpr[i] = event.tpr
    fpr[i] = event.fpr
    #print tpr[i],fpr[i]
    i+=1

graph_std = TGraph(10000,fpr,tpr)
graph_std.SetMarkerColor(2)
graph_std.SetLineColor(2)
graph_std.SetLineWidth(3)


tpr = np.zeros(tree.GetEntries())
fpr = np.zeros(tree.GetEntries())
i = 0
for event in tree:
    tpr[i] = event.tpr
    fpr[i] = event.fpr
    #print tpr[i],fpr[i]
    i+=1

graph_NN = TGraph(10000,fpr,tpr)
graph_NN.SetMarkerColor(4)
graph_NN.SetLineColor(4)
graph_NN.SetLineWidth(3)

leg = TLegend(0.6,0.2,0.9,0.5)
leg.AddEntry(graph_std,"Standard ID","l")
leg.AddEntry(graph_NN,"RecNN ID","l")


can = TCanvas()
can.SetLogx()
basegraph.Draw()
leg.Draw("same")
graph_NN.Draw("same")
graph_std.Draw("same")
