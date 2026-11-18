import ROOT
import os
import math
import copy
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class JetVetoProducer(Module):

    def __init__(self):

        jveto_fN = ["hotjets-UL16.root"]
        jveto_h1 = ["h2hot_ul16_plus_hbm2_hbp12_qie11"]
        jveto_h2 = ["h2hot_mc"]

        jveto_f = ["%s/src/TZWi/TopAnalysis/data/JetVeto/" % os.environ['CMSSW_BASE'] + f for f in jveto_fN]

        self.jveto_f = ROOT.std.vector(str)(len(jveto_f))
        self.jveto_h1 = ROOT.std.vector(str)(len(jveto_f))
        self.jveto_h2 = ROOT.std.vector(str)(len(jveto_f))
        for i in range(len(jveto_f)): self.jveto_f[i] = jveto_f[i]; self.jveto_h1[i] = jveto_h1[i]; self.jveto_h2[i] = jveto_h2[i];

        if "libTZWiTopAnalysis.so" not in ROOT.gSystem.GetLibraries():
            ROOT.gSystem.Load("libTZWiTopAnalysis.so")
        if not hasattr(ROOT, "JetVetoCorrector"):
            ROOT.gROOT.ProcessLine(".L %s/src/TZWi/TopAnalysis/interface/JetVetoCorrector.h" % os.environ['CMSSW_BASE'])

    def beginJob(self):
        self._worker_jveto1 = ROOT.JetVetoCorrector(self.jveto_f,self.jveto_h1)
        self._worker_jveto2 = ROOT.JetVetoCorrector(self.jveto_f,self.jveto_h2)

    def endJob(self):
        # Explicitly delete C++ worker objects to prevent ROOT GC segfaults at exit
        if hasattr(self, '_worker_jveto1'): del self._worker_jveto1
        if hasattr(self, '_worker_jveto2'): del self._worker_jveto2

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
#        self.out.branch("JetVeto", "F", lenVar="nGoodJet")
        self.out.branch("JetVetoSum", "F")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        jetveto = []
        jetvetosum = 0.

        for jindex in range(event._tree.b_out_nGoodJet):
            jeta = (event._tree.b_out_GoodJet_eta)[jindex]
            jphi = (event._tree.b_out_GoodJet_phi)[jindex]
            jetvetoElement1 = self._worker_jveto1.getJV(jeta,jphi)
            jetvetoElement2 = self._worker_jveto2.getJV(jeta,jphi)
            jetveto.append(jetvetoElement1)
            jetveto.append(jetvetoElement2)
            jetvetosum += jetvetoElement1
            jetvetosum += jetvetoElement2

#        setattr(event._tree, "b_out_JetVeto", jetveto)
        setattr(event._tree, "b_out_JetVetoSum", jetvetosum)

#        self.out.fillBranch("JetVeto", jetveto)
        self.out.fillBranch("JetVetoSum", jetvetosum)

        return True

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

JVProducer = lambda : JetVetoProducer()
