from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
import os
#import numpy as np
ROOT.PyConfig.IgnoreCommandLineOptions = True


class puWeightProducer(Module):
    def __init__(self,
                 myfile,
                 targetfile_central,
                 targetfile_plus,
                 targetfile_minus,
                 myhist="pileup",
                 targethist="pileup",
                 name="puWeight",
                 norm=True,
                 verbose=False,
                 nvtx_var="Pileup_nTrueInt",
                 doSysVar=True
     ):

        self.targeth = self.loadHisto(targetfile_central, targethist)
        if doSysVar:
            self.targeth_plus = self.loadHisto(targetfile_plus, targethist)
            self.targeth_minus = self.loadHisto(targetfile_minus, targethist)

        self.fixLargeWeights = True  # temporary fix
        if myfile != "auto":
            self.autoPU = False
            self.myh = self.loadHisto(myfile, myhist)
        else:
            self.fixLargeWeights = False  # AR: it seems to crash with it, to be deugged
            self.autoPU = True
            ROOT.gROOT.cd()
            self.myh = self.targeth.Clone("autoPU")
            self.myh.Reset()
        self.name = name
        self.norm = norm
        self.verbose = verbose
        self.nvtxVar = nvtx_var
        self.doSysVar = doSysVar

        # Load it via ROOT ACLIC. NB: this creates the object file in the
        # CMSSW directory, causing problems if many jobs are working from the
        # same CMSSW directory
        if "libTZWiTopAnalysis.so" not in ROOT.gSystem.GetLibraries():
            ROOT.gSystem.Load("libTZWiTopAnalysis.so")
        if not hasattr(ROOT, "WeightCalculatorFromHistogram"):
            ROOT.gROOT.ProcessLine(".L %s/src/TZWi/TopAnalysis/interface/WeightCalculatorFromHistogram.h" % os.environ['CMSSW_BASE'])

    def loadHisto(self, filename, hname):
        tf = ROOT.TFile.Open(filename)
        if not tf or tf.IsZombie():
            raise RuntimeError("Cannot open ROOT file: %s" % filename)

        hist = tf.Get(hname)
        if not hist:
            tf.Close()
            raise RuntimeError("Histogram '%s' not found in file: %s" % (hname, filename))

        hist = hist.Clone("%s__%s" % (hname, os.path.basename(filename).replace(".", "_")))
        hist.SetDirectory(0)
        tf.Close()
        return hist

    def beginJob(self):
        pass

    def endJob(self):
        # Explicitly delete C++ histogram objects to prevent ROOT GC segfaults at exit
        if hasattr(self, 'targeth'): del self.targeth
        if hasattr(self, 'targeth_plus'): del self.targeth_plus
        if hasattr(self, 'targeth_minus'): del self.targeth_minus
        if hasattr(self, 'myh'): del self.myh

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        if self.autoPU:
            self.myh.Reset()
            print("Computing PU profile for this file")
            ROOT.gROOT.cd()
            inputFile.Get("Events").Project("autoPU",
                                            self.nvtxVar)  # doitfrom inputFile
            if outputFile:
                outputFile.cd()
                self.myh.Write()
        self._worker = ROOT.WeightCalculatorFromHistogram(
            self.myh, self.targeth, self.norm, self.fixLargeWeights,
            self.verbose)
        self.out = wrappedOutputTree
        self.out.branch(self.name, "F")
        if self.doSysVar:
            self._worker_plus = ROOT.WeightCalculatorFromHistogram(
                self.myh, self.targeth_plus, self.norm, self.fixLargeWeights,
                self.verbose)
            self._worker_minus = ROOT.WeightCalculatorFromHistogram(
                self.myh, self.targeth_minus, self.norm, self.fixLargeWeights,
                self.verbose)
            self.out.branch(self.name + "Up", "F")
            self.out.branch(self.name + "Down", "F")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        # Clean up C++ worker objects to prevent cppyy double-free segfaults
        if hasattr(self, '_worker'): del self._worker
        if hasattr(self, '_worker_plus'): del self._worker_plus
        if hasattr(self, '_worker_minus'): del self._worker_minus

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        if hasattr(event, self.nvtxVar):
            nvtx = int(getattr(event, self.nvtxVar))
            weight = self._worker.getWeight(
                nvtx) if nvtx < self.myh.GetNbinsX() else 1
            if self.doSysVar:
                weight_plus = self._worker_plus.getWeight(
                    nvtx) if nvtx < self.myh.GetNbinsX() else 1
                weight_minus = self._worker_minus.getWeight(
                    nvtx) if nvtx < self.myh.GetNbinsX() else 1
        else:
            weight = 1
        self.out.fillBranch(self.name, weight)
        if self.doSysVar:
            self.out.fillBranch(self.name + "Up", weight_plus)
            self.out.fillBranch(self.name + "Down", weight_minus)
        return True


# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

pufile_mc2016 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/pileup_profile_Summer16.root" % os.environ[
    'CMSSW_BASE']
pufile_data2016 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/PileupData_GoldenJSON_Full2016.root" % os.environ[
    'CMSSW_BASE']
puWeight_2016 = lambda: puWeightProducer(pufile_mc2016,
                                         pufile_data2016,
                                         "pu_mc",
                                         "pileup",
                                         verbose=False,
                                         doSysVar=True)
puAutoWeight_2016 = lambda: puWeightProducer(
    "auto", pufile_data2016, "pu_mc", "pileup", verbose=False)

pufile_data2017 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/PileupHistogram-goldenJSON-13tev-2017-99bins_withVar.root" % os.environ[
    'CMSSW_BASE']
pufile_mc2017 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/mcPileup2017.root" % os.environ[
    'CMSSW_BASE']
puWeight_2017 = lambda: puWeightProducer(pufile_mc2017,
                                         pufile_data2017,
                                         "pu_mc",
                                         "pileup",
                                         verbose=False,
                                         doSysVar=True)
puAutoWeight_2017 = lambda: puWeightProducer(
    "auto", pufile_data2017, "pu_mc", "pileup", verbose=False)

pufile_data2018 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/PileupHistogram-goldenJSON-13tev-2018-100bins_withVar.root" % os.environ[
    'CMSSW_BASE']
pufile_mc2018 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/mcPileup2018.root" % os.environ[
    'CMSSW_BASE']
puWeight_2018 = lambda: puWeightProducer(pufile_mc2018,
                                         pufile_data2018,
                                         "pu_mc",
                                         "pileup",
                                         verbose=False,
                                         doSysVar=True)
puAutoWeight_2018 = lambda: puWeightProducer(
    "auto", pufile_data2018, "pu_mc", "pileup", verbose=False)

# Ultra legacy

# 2016
pufile_dataUL2016 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/PileupHistogram-UL2016-100bins_withVar.root" % os.environ[
    'CMSSW_BASE']
pufile_mcUL2016 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/mcPileupUL2016.root" % os.environ[
    'CMSSW_BASE']
puWeight_UL2016 = lambda: puWeightProducer(pufile_mcUL2016,
                                           pufile_dataUL2016,
                                           "pu_mc",
                                           "pileup",
                                           verbose=False,
                                           doSysVar=True)
puAutoWeight_UL2016 = lambda: puWeightProducer(
    "auto", pufile_dataUL2016, "pu_mc", "pileup", verbose=False)

# 2017
pufile_dataUL2017 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/PileupHistogram-UL2017-100bins_withVar.root" % os.environ[
    'CMSSW_BASE']
pufile_mcUL2017 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/mcPileupUL2017.root" % os.environ[
    'CMSSW_BASE']
puWeight_UL2017 = lambda: puWeightProducer(pufile_mcUL2017,
                                           pufile_dataUL2017,
                                           "pu_mc",
                                           "pileup",
                                           verbose=False,
                                           doSysVar=True)
puAutoWeight_UL2017 = lambda: puWeightProducer(
    "auto", pufile_dataUL2017, "pu_mc", "pileup", verbose=False)

# 2018
pufile_dataUL2018 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/PileupHistogram-UL2018-100bins_withVar.root" % os.environ[
    'CMSSW_BASE']
pufile_mcUL2018 = "%s/src/PhysicsTools/NanoAODTools/python/postprocessing/data/pileup/mcPileupUL2018.root" % os.environ[
    'CMSSW_BASE']
puWeight_UL2018 = lambda: puWeightProducer(pufile_mcUL2018,
                                           pufile_dataUL2018,
                                           "pu_mc",
                                           "pileup",
                                           verbose=False,
                                           doSysVar=True)
puAutoWeight_UL2018 = lambda: puWeightProducer(
    "auto", pufile_dataUL2018, "pu_mc", "pileup", verbose=False)

# NewUL2018
pufile_dataNewUL2018_central = "%s/src/TZWi/TopAnalysis/data/pileup/PileupHistogram-goldenJSON-13tev-2018-69200ub-99bins_New.root" % os.environ['CMSSW_BASE']
pufile_dataNewUL2018_plus = "%s/src/TZWi/TopAnalysis/data/pileup/PileupHistogram-goldenJSON-13tev-2018-72400ub-99bins_New.root" % os.environ['CMSSW_BASE']
pufile_dataNewUL2018_minus = "%s/src/TZWi/TopAnalysis/data/pileup/PileupHistogram-goldenJSON-13tev-2018-66000ub-99bins_New.root" % os.environ['CMSSW_BASE']
pufile_mcNewUL2018 = "%s/src/TZWi/TopAnalysis/data/pileup/mcPileupUL2018.root" % os.environ['CMSSW_BASE']
puWeight_NewUL2018 = lambda: puWeightProducer(pufile_mcNewUL2018,
                                           pufile_dataNewUL2018_central,
                                           pufile_dataNewUL2018_plus,
                                           pufile_dataNewUL2018_minus,
                                           "pu_mc",
                                           "pileup_new",
                                           verbose=False,
                                           doSysVar=True)
