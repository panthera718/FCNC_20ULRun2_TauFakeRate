import ROOT
import os
import math
import copy
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module


class FakeRateProducer(Module):

    TAU_FR = {
        "pt_bins_motherjet_approx_GeV": [
            (0, 20),
            (20, 25),
            (25, 30),
            (30, 40),
            (40, 50),
            (50, 70),
            (70, 100),
            (100, 300),
        ],
        "2016preVFP": {
            "prong1": {
                "absEta_0p0_0p8": {
                    "fr":  [0.122718, 0.480550, 0.341556, 0.211988, 0.161771, 0.142609, 0.132951, 0.162980],
                    "err": [0.037914, 0.019217, 0.006714, 0.003259, 0.003841, 0.004283, 0.006798, 0.011943],
                },
                "absEta_0p8_1p5": {
                    "fr":  [0.142591, 0.463339, 0.406011, 0.244374, 0.185438, 0.156454, 0.145318, 0.152956],
                    "err": [0.044771, 0.031654, 0.010962, 0.004134, 0.004399, 0.004604, 0.007423, 0.012313],
                },
                "absEta_1p5_2p4": {
                    "fr":  [0.071296, 0.201167, 0.365202, 0.217102, 0.156192, 0.142789, 0.125209, 0.159763],
                    "err": [0.032409, 0.029181, 0.018839, 0.004914, 0.004338, 0.004574, 0.006857, 0.012505],
                },
            },
            "prong23": {
                "absEta_0p0_2p4": {
                    "fr":  [0.130239, 0.145300, 0.149590, 0.106148, 0.092714, 0.088772, 0.090134, 0.096582],
                    "err": [0.023992, 0.010842, 0.004972, 0.002123, 0.002266, 0.002414, 0.003785, 0.005810],
                },
            },
        },
        "2016postVFP": {
            "prong1": {
                "absEta_0p0_0p8": {
                    "fr":  [0.203, 0.278, 0.156, 0.094, 0.069, 0.074, 0.067, 0.045],
                    "err": [0.075, 0.016, 0.010, 0.008, 0.007, 0.005, 0.012, 0.022],
                },
                "absEta_0p8_1p5": {
                    "fr":  [0.048, 0.278, 0.205, 0.144, 0.106, 0.081, 0.079, 0.091],
                    "err": [0.048, 0.055, 0.017, 0.010, 0.006, 0.006, 0.006, 0.020],
                },
                "absEta_1p5_2p4": {
                    "fr":  [0.228, 0.221, 0.263, 0.179, 0.118, 0.099, 0.076, 0.102],
                    "err": [0.098, 0.090, 0.029, 0.013, 0.010, 0.007, 0.015, 0.017],
                },
            },
            "prong23": {
                "absEta_0p0_2p4": {
                    "fr":  [0.107, 0.149, 0.096, 0.074, 0.066, 0.065, 0.060, 0.076],
                    "err": [0.031, 0.027, 0.008, 0.006, 0.005, 0.004, 0.004, 0.008],
                },
            },
        },
        "2017": {
            "prong1": {
                "absEta_0p0_0p8": {
                    "fr":  [0.267, 0.267, 0.173, 0.118, 0.094, 0.080, 0.067, 0.078],
                    "err": [0.068, 0.010, 0.009, 0.008, 0.006, 0.004, 0.005, 0.016],
                },
                "absEta_0p8_1p5": {
                    "fr":  [0.161, 0.309, 0.199, 0.145, 0.119, 0.094, 0.085, 0.099],
                    "err": [0.038, 0.031, 0.010, 0.008, 0.007, 0.005, 0.005, 0.018],
                },
                "absEta_1p5_2p4": {
                    "fr":  [0.080, 0.254, 0.177, 0.141, 0.106, 0.089, 0.089, 0.117],
                    "err": [0.045, 0.020, 0.010, 0.007, 0.005, 0.004, 0.020, 0.012],
                },
            },
            "prong23": {
                "absEta_0p0_2p4": {
                    "fr":  [0.118, 0.124, 0.097, 0.078, 0.070, 0.064, 0.062, 0.079],
                    "err": [0.020, 0.016, 0.007, 0.006, 0.005, 0.004, 0.003, 0.006],
                },
            },
        },
        "2018": {
            "prong1": {
                "absEta_0p0_0p8": {
                    "fr":  [0.219258, 0.378651, 0.261981, 0.181056, 0.145819, 0.135647, 0.140057, 0.151641],
                    "err": [0.023079, 0.008137, 0.003397, 0.001807, 0.002144, 0.002444, 0.004052, 0.006903],
                },
                "absEta_0p8_1p5": {
                    "fr":  [0.187170, 0.417229, 0.327555, 0.218217, 0.170983, 0.152350, 0.155243, 0.165704],
                    "err": [0.024625, 0.013946, 0.005495, 0.002314, 0.002455, 0.002641, 0.004470, 0.007102],
                },
                "absEta_1p5_2p4": {
                    "fr":  [0.151205, 0.267524, 0.391163, 0.224208, 0.158861, 0.140601, 0.129692, 0.142044],
                    "err": [0.020342, 0.015048, 0.009767, 0.003016, 0.002778, 0.002920, 0.004813, 0.008124],
                },
            },
            "prong23": {
                "absEta_0p0_2p4": {
                    "fr":  [0.102921, 0.147068, 0.134312, 0.105321, 0.091725, 0.088478, 0.091433, 0.092294],
                    "err": [0.009295, 0.004701, 0.002429, 0.001175, 0.001276, 0.001365, 0.002206, 0.003320],
                },
            },
        },
    }

    def __init__(self, era=None):

        mu_fN = ["2018_fakerates_MR_mu33_LowVersion.root"]
        mu_h = ["fakeratesMRmu"]
        mu_err_h = ["staterr"]

        el_fN = ["2018_fakerates_MR_ele27_LowVersion.root"]
        el_h = ["fakeratesMRele"]
        el_err_h = ["staterr"]

        mu_f = ["%s/src/TZWi/TopAnalysis/data/FakeRate/" % os.environ['CMSSW_BASE'] + f for f in mu_fN]
        el_f = ["%s/src/TZWi/TopAnalysis/data/FakeRate/" % os.environ['CMSSW_BASE'] + f for f in el_fN]

        self.mu_f = ROOT.std.vector(str)(len(mu_f))
        self.mu_h = ROOT.std.vector(str)(len(mu_f))
        self.mu_err_h = ROOT.std.vector(str)(len(mu_f))
        for i in range(len(mu_f)):
            self.mu_f[i] = mu_f[i]
            self.mu_h[i] = mu_h[i]
            self.mu_err_h[i] = mu_err_h[i]

        self.el_f = ROOT.std.vector(str)(len(el_f))
        self.el_h = ROOT.std.vector(str)(len(el_f))
        self.el_err_h = ROOT.std.vector(str)(len(el_f))
        for i in range(len(el_f)):
            self.el_f[i] = el_f[i]
            self.el_h[i] = el_h[i]
            self.el_err_h[i] = el_err_h[i]

        self.explicit_era = era if era is not None else os.environ.get("FAKERATE_ERA", None)
        self.inputFileName = ""
        self._resolved_era = None
        self._warned_ambiguous_2016 = False
        self._warned_unknown_era = False
        self._warned_tau_no_matched_jet = False

        if "libTZWiTopAnalysis.so" not in ROOT.gSystem.GetLibraries():
            ROOT.gSystem.Load("libTZWiTopAnalysis.so")
        if not hasattr(ROOT, "FakeRateCorrector"):
            ROOT.gROOT.ProcessLine(".L %s/src/TZWi/TopAnalysis/interface/FakeRateCorrector.h" % os.environ['CMSSW_BASE'])

    def beginJob(self):
        self._worker_mu = ROOT.FakeRateCorrector(self.mu_f, self.mu_h)
        self._worker_mu_err = ROOT.FakeRateCorrector(self.mu_f, self.mu_err_h)
        self._worker_el = ROOT.FakeRateCorrector(self.el_f, self.el_h)
        self._worker_el_err = ROOT.FakeRateCorrector(self.el_f, self.el_err_h)

    def endJob(self):
        if hasattr(self, '_worker_mu'):
            del self._worker_mu
        if hasattr(self, '_worker_mu_err'):
            del self._worker_mu_err
        if hasattr(self, '_worker_el'):
            del self._worker_el
        if hasattr(self, '_worker_el_err'):
            del self._worker_el_err

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.inputFileName = inputFile.GetName() if inputFile and hasattr(inputFile, "GetName") else ""
        self._resolved_era = self._resolve_tau_era()

        self.out.branch("Lepton1_FR", "F")
        self.out.branch("Lepton1_FRerr", "F")
        self.out.branch("Lepton2_FR", "F")
        self.out.branch("Lepton2_FRerr", "F")
        self.out.branch("Lepton3_FR", "F")
        self.out.branch("Lepton3_FRerr", "F")
        self.out.branch("FakeRateWeight", "F")
        self.out.branch("FakeRateWeightError", "F")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def _resolve_tau_era(self):
        if self.explicit_era in self.TAU_FR:
            return self.explicit_era

        name = self.inputFileName.lower()
        if "2018" in name:
            return "2018"
        if "2017" in name:
            return "2017"

        pre_tokens = [
            "2016apv", "prevfp", "pre-vfp", "hipm",
            "run2016b", "run2016c", "run2016d", "run2016e", "run2016f-hipm",
        ]
        post_tokens = [
            "2016postvfp", "postvfp", "post-vfp",
            "run2016g", "run2016h", "run2016f-ul2016",
        ]

        for tok in pre_tokens:
            if tok in name:
                return "2016preVFP"
        for tok in post_tokens:
            if tok in name and "hipm" not in name:
                return "2016postVFP"

        if "2016" in name:
            if not self._warned_ambiguous_2016:
                print("[FakeRateProducer] Warning: could not distinguish 2016preVFP and 2016postVFP from input file '%s'. Defaulting tau fake rate era to 2016preVFP. Set FAKERATE_ERA or instantiate FakeRateProducer(era='2016postVFP') to override." % self.inputFileName)
                self._warned_ambiguous_2016 = True
            return "2016preVFP"

        if not self._warned_unknown_era:
            print("[FakeRateProducer] Warning: could not infer tau fake rate era from input file '%s'. Defaulting to 2018." % self.inputFileName)
            self._warned_unknown_era = True
        return "2018"

    @staticmethod
    def _get_tau_prong_group(decay_mode):
        dm = int(decay_mode)
        if dm in (0, 1, 2):
            return "prong1"
        if dm in (10, 11):
            return "prong23"
        if dm >= 10:
            return "prong23"
        return "prong1"

    @staticmethod
    def _get_tau_eta_key(abs_eta, prong_group):
        if prong_group == "prong23":
            return "absEta_0p0_2p4"
        if abs_eta < 0.8:
            return "absEta_0p0_0p8"
        if abs_eta < 1.5:
            return "absEta_0p8_1p5"
        return "absEta_1p5_2p4"

    def _get_tau_pt_bin_index(self, mother_jet_pt):
        bins = self.TAU_FR["pt_bins_motherjet_approx_GeV"]
        pt = float(mother_jet_pt)
        if pt < bins[0][0]:
            return 0
        for i, (ptmin, ptmax) in enumerate(bins):
            if pt >= ptmin and pt < ptmax:
                return i
        return len(bins) - 1

    def _get_tau_fr(self, era, mother_jet_pt, abs_eta, decay_mode):
        prong_group = self._get_tau_prong_group(decay_mode)
        eta_key = self._get_tau_eta_key(abs_eta, prong_group)
        ibin = self._get_tau_pt_bin_index(mother_jet_pt)
        fr_map = self.TAU_FR[era][prong_group][eta_key]
        return float(fr_map["fr"][ibin]), float(fr_map["err"][ibin])

    @staticmethod
    def _get_ptcone_from_tree(tree, idx):
        is_tight = getattr(tree, "b_out_Lepton%d_isTight" % idx)
        lep_pt = getattr(tree, "b_out_Lepton%d_pt" % idx)
        jet_pt = getattr(tree, "b_out_Lepton%d_Jet_pt" % idx)
        lep_pfiso = getattr(tree, "b_out_Lepton%d_PFIso" % idx)
        if is_tight:
            return lep_pt
        if jet_pt > 0:
            return 0.7 * jet_pt
        return 0.7 * lep_pt * (1.0 + lep_pfiso)

    def _get_tau_inputs_from_tree(self, tree, idx):
        tau_decay_attr = "b_out_Lepton%d_tauDecayMode" % idx
        if not hasattr(tree, tau_decay_attr):
            raise RuntimeError(
                "Tau fake rate requires Lepton%d_tauDecayMode, but this branch is missing. "
                "Update fcncTriLepton_allmodes_unified to store tau decayMode/prong information before running FakeRateProducer." % idx
            )
        decay_mode = int(getattr(tree, tau_decay_attr))
        mother_jet_pt = getattr(tree, "b_out_Lepton%d_Jet_pt" % idx)
        if mother_jet_pt <= 0.0:
            if not self._warned_tau_no_matched_jet:
                print("[FakeRateProducer] Warning: tau candidate without matched jet encountered. Falling back to tau pT for tau fake-rate lookup.")
                self._warned_tau_no_matched_jet = True
            mother_jet_pt = getattr(tree, "b_out_Lepton%d_pt" % idx)
        abs_eta = abs(getattr(tree, "b_out_Lepton%d_eta" % idx))
        return float(mother_jet_pt), float(abs_eta), decay_mode

    def _get_lepton_fr(self, tree, idx):
        pdgid = abs(getattr(tree, "b_out_Lepton%d_pdgId" % idx))

        if pdgid == 11:
            ptcone = self._get_ptcone_from_tree(tree, idx)
            eta = abs(getattr(tree, "b_out_Lepton%d_eta" % idx))
            return float(self._worker_el.getFR(ptcone, eta)), float(self._worker_el_err.getFR(ptcone, eta))

        if pdgid == 13:
            ptcone = self._get_ptcone_from_tree(tree, idx)
            eta = abs(getattr(tree, "b_out_Lepton%d_eta" % idx))
            return float(self._worker_mu.getFR(ptcone, eta)), float(self._worker_mu_err.getFR(ptcone, eta))

        if pdgid == 15:
            mother_jet_pt, abs_eta, decay_mode = self._get_tau_inputs_from_tree(tree, idx)
            return self._get_tau_fr(self._resolved_era, mother_jet_pt, abs_eta, decay_mode)

        return 0.0, 0.0

    @staticmethod
    def _fr_to_factor(fr):
        fr = float(fr)
        if fr >= 1.0:
            fr = 1.0 - 1.0e-6
        if fr <= -1.0:
            fr = -1.0 + 1.0e-6
        return -fr / (1.0 - fr)

    @staticmethod
    def _frerr_to_factorerr(fr, fr_err):
        fr = float(fr)
        fr_err = abs(float(fr_err))
        if fr >= 1.0:
            fr = 1.0 - 1.0e-6
        if fr <= -1.0:
            fr = -1.0 + 1.0e-6
        return fr_err / ((1.0 - fr) ** 2)

    @staticmethod
    def _event_has_selected_tau(tree):
        return any(
            abs(int(getattr(tree, "b_out_Lepton%d_pdgId" % idx))) == 15
            for idx in (1, 2, 3)
        )

    @staticmethod
    def _event_has_prompt_selected_tau(tree):
        for idx in (1, 2, 3):
            if abs(int(getattr(tree, "b_out_Lepton%d_pdgId" % idx))) != 15:
                continue

            tau_genpartflav_attr = "b_out_Lepton%d_tauGenPartFlav" % idx
            if not hasattr(tree, tau_genpartflav_attr):
                raise RuntimeError(
                    "Tau prompt-subtraction requires Lepton%d_tauGenPartFlav, but this branch is missing. "
                    "Update fcncTriLepton_allmodes_unified.py before running FakeRateProducer." % idx
                )

            if int(getattr(tree, tau_genpartflav_attr)) == 5:
                return True
        return False

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        tree = event._tree

        fr_lepton1, fr_lepton1_err = self._get_lepton_fr(tree, 1)
        fr_lepton2, fr_lepton2_err = self._get_lepton_fr(tree, 2)
        fr_lepton3, fr_lepton3_err = self._get_lepton_fr(tree, 3)

        fake_terms = []
        for is_fake, fr, fr_err in [
            (tree.b_out_Lepton1_isFake, fr_lepton1, fr_lepton1_err),
            (tree.b_out_Lepton2_isFake, fr_lepton2, fr_lepton2_err),
            (tree.b_out_Lepton3_isFake, fr_lepton3, fr_lepton3_err),
        ]:
            if is_fake:
                fake_terms.append((self._fr_to_factor(fr), self._frerr_to_factorerr(fr, fr_err)))

        if not fake_terms:
            FRweight = 0.0
            FRweightErr = 0.0
        else:
            FRweight = -1.0
            for factor, _ in fake_terms:
                FRweight *= factor

            FRweightErr2 = 0.0
            for i, (_, factor_err) in enumerate(fake_terms):
                other_prod = -1.0
                for j, (other_factor, _) in enumerate(fake_terms):
                    if i == j:
                        continue
                    other_prod *= other_factor
                FRweightErr2 += (other_prod * factor_err) ** 2
            FRweightErr = math.sqrt(FRweightErr2)

        self.out.fillBranch("Lepton1_FR", fr_lepton1)
        self.out.fillBranch("Lepton1_FRerr", fr_lepton1_err)
        self.out.fillBranch("Lepton2_FR", fr_lepton2)
        self.out.fillBranch("Lepton2_FRerr", fr_lepton2_err)
        self.out.fillBranch("Lepton3_FR", fr_lepton3)
        self.out.fillBranch("Lepton3_FRerr", fr_lepton3_err)
        self.out.fillBranch("FakeRateWeight", FRweight)
        self.out.fillBranch("FakeRateWeightError", FRweightErr)

        return True


FRProducer = lambda: FakeRateProducer()
FRProducer_2016preVFP = lambda: FakeRateProducer(era="2016preVFP")
FRProducer_2016postVFP = lambda: FakeRateProducer(era="2016postVFP")
FRProducer_2017 = lambda: FakeRateProducer(era="2017")
FRProducer_2018 = lambda: FakeRateProducer(era="2018")
