import ROOT
import os
import math
import copy
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class JetPUIDSFProducer(Module):

    def __init__(self):

        jpuidsf_fN = ["PUID_106XTraining_ULRun2_EffSFandUncties_v1.root"]
        jpuidsf_h = ["h2_eff_sfUL2017_L"]
        jpuidsf_herr = ["h2_eff_sfUL2017_L_Systuncty"]

        jpuidsf_f = ["%s/src/TZWi/TopAnalysis/data/JetPUIDSF/" % os.environ['CMSSW_BASE'] + f for f in jpuidsf_fN]

        self.jpuidsf_f = ROOT.std.vector(str)(len(jpuidsf_f))
        self.jpuidsf_h = ROOT.std.vector(str)(len(jpuidsf_f))
        self.jpuidsf_herr = ROOT.std.vector(str)(len(jpuidsf_f))
        for i in range(len(jpuidsf_f)): self.jpuidsf_f[i] = jpuidsf_f[i]; self.jpuidsf_h[i] = jpuidsf_h[i]; self.jpuidsf_herr[i] = jpuidsf_herr[i];

        if "libTZWiTopAnalysis.so" not in ROOT.gSystem.GetLibraries():
            ROOT.gSystem.Load("libTZWiTopAnalysis.so")
        if not hasattr(ROOT, "JetPUIDSFCorrector"):
            ROOT.gROOT.ProcessLine(".L %s/src/TZWi/TopAnalysis/interface/JetPUIDSFCorrector.h" % os.environ['CMSSW_BASE'])

    def beginJob(self):
        self._worker_jpuidsf = ROOT.JetPUIDSFCorrector(self.jpuidsf_f,self.jpuidsf_h)
        self._worker_jpuidsferr = ROOT.JetPUIDSFCorrector(self.jpuidsf_f,self.jpuidsf_herr)

    def endJob(self):
        # Explicitly delete C++ worker objects to prevent ROOT GC segfaults at exit
        if hasattr(self, '_worker_jpuidsf'): del self._worker_jpuidsf
        if hasattr(self, '_worker_jpuidsferr'): del self._worker_jpuidsferr

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
#        self.out.branch("JetPUID_eachSF", "F", lenVar="nGoodJet")
#        self.out.branch("JetPUID_eachSFerr", "F", lenVar="nGoodJet")
        self.out.branch("JetPUID_SF", "F")
        self.out.branch("JetPUID_SFerr", "F")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        jetpuid_eachsf = []
        jetpuid_eachsferr = []
        jetpuid_sf = 1.
        jetpuid_sferr_sqsum = 0.

        for jetindex in range(event._tree.b_out_nGoodJet):
            jpt = (event._tree.b_out_GoodJet_pt)[jetindex]
            jeta = (event._tree.b_out_GoodJet_eta)[jetindex]
            if jpt < 50.:
                jetpuidsfElement = self._worker_jpuidsf.getJPUIDSF(jpt,jeta)
                jetpuidsferrElement = self._worker_jpuidsferr.getJPUIDSF(jpt,jeta)
                jetpuid_eachsf.append(jetpuidsfElement)
                jetpuid_eachsferr.append(jetpuidsferrElement)
                jetpuid_sf *= jetpuidsfElement
                jetpuid_sferr_sqsum += jetpuidsferrElement**2

        jetpuid_sferr = math.sqrt(jetpuid_sferr_sqsum)

#        setattr(event._tree, "b_out_JetPUID_eachSF", jetpuid_eachsf)
#        setattr(event._tree, "b_out_JetPUID_eachSFerr", jetpuid_eachsferr)
        setattr(event._tree, "b_out_JetPUID_SF", jetpuid_sf)
        setattr(event._tree, "b_out_JetPUID_SFerr", jetpuid_sferr)

#        self.out.fillBranch("JetPUID_eachSF", jetpuid_eachsf)
#        self.out.fillBranch("JetPUID_eachSFerr", jetpuid_eachsferr)
        self.out.fillBranch("JetPUID_SF", jetpuid_sf)
        self.out.fillBranch("JetPUID_SFerr", jetpuid_sferr)

        return True

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

JPUIDSFProducer = lambda : JetPUIDSFProducer()
