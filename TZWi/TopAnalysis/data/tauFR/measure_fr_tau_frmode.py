#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import argparse
from array import array
from pathlib import Path
import ROOT
import yaml

ROOT.gROOT.SetBatch(True)

Z_MASS = 91.2

#PT_BINS = [0.0, 20.0, 25.0, 30.0, 40.0, 50.0, 70.0, 100.0, 300.0]
PT_BINS = [15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 70.0, 100.0, 300.0]
#PT_BINS = [15.0, 30.0, 50.0, 70.0, 100.0, 300.0]

CATEGORIES = [
    ("prong1_eta0", "prong1", 0.0, 0.8),
    ("prong1_eta1", "prong1", 0.8, 1.5),
    ("prong1_eta2", "prong1", 1.5, 2.4),
    ("prong23_eta", "prong23", 0.0, 2.4),
]

DEFAULT_MC_WEIGHT = "(abs(genWeight)/genWeight)*puWeight*JetPUID_SF*Electron_RecoSF*Electron_SF*Muon_SF*BtagWeight*L1PreFiringWeight_Nom"
DEFAULT_NPLMC_WEIGHT = "(abs(genWeight)/genWeight)*puWeight*JetPUID_SF*FakeElectron_RecoSF*FakeElectron_SF*FakeMuon_SF*BtagWeight*L1PreFiringWeight_Nom"
DEFAULT_ALLOWED_MODES = ("FRTaElEl", "FRTaMuMu")
DEFAULT_GROUPING_PATH = "config/grouping.yaml"
DEFAULT_XSEC_PATH = "config/crosssection.yaml"
DEFAULT_LUMI_FB = 41.500

XSEC_KEYS = (
    "crosssection", "cross_section", "xsec", "xSection", "xs",
    "cross section", "XSection", "Xsec",
)
SUMW_KEYS = (
    "nEventsGenWeighted", "nEventGenWeighted", "neventsgenweighted",
    "genEventSumw", "geneventsumw", "sumw", "sumW", "sum_gen_weight",
    "sumGenWeight", "sumgenweight", "Entries", "entries",
)
DATASET_ALIAS_KEYS = (
    "dataset", "datasets", "name", "names", "path", "paths", "sample", "samples"
)


def read_file_list(path):
    files = []
    with open(path) as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            files.append(s)
    return files


def canonical_dataset_name(name):
    if name is None:
        return None
    s = str(name).strip()
    if not s:
        return None
    if s.startswith("/"):
        s = s[1:].replace("/", ".")
    s = s.rstrip("/")
    for suf in (".NANOAODSIM", ".NANOAOD", ".MINIAODSIM", ".MINIAOD"):
        if s.endswith(suf):
            s = s[:-len(suf)]
    return s


def dataset_short_name(name):
    ds = canonical_dataset_name(name)
    if ds is None:
        return None
    return ds.split(".")[0]


def dataset_dir_from_file(path):
    return canonical_dataset_name(Path(path).parent.name)


def path_has_allowed_mode(path, allowed_modes):
    return any(f"/{mode}/" in path for mode in allowed_modes)


def filter_files_by_mode(files, allowed_modes):
    return [f for f in files if path_has_allowed_mode(f, allowed_modes)]


def build_chain(tree_name, files):
    chain = ROOT.TChain(tree_name)
    for f in files:
        chain.Add(f)
    return chain


def make_hist(name, title):
    h = ROOT.TH1D(name, title, len(PT_BINS) - 1, array("d", PT_BINS))
    h.Sumw2()
    return h


def make_result_hists(prefix):
    out = {}
    for cat_name, _, _, _ in CATEGORIES:
        out[cat_name] = make_hist(
            f"{prefix}_{cat_name}",
            f"{prefix}_{cat_name};matched jet pT [GeV];Events"
        )
    return out


def p4(ev, idx):
    lv = ROOT.TLorentzVector()
    lv.SetPtEtaPhiM(
        float(getattr(ev, f"Lepton{idx}_pt")),
        float(getattr(ev, f"Lepton{idx}_eta")),
        float(getattr(ev, f"Lepton{idx}_phi")),
        float(getattr(ev, f"Lepton{idx}_mass")),
    )
    return lv


def charge_from_pdgid(pdgid):
    if pdgid > 0:
        return -1
    if pdgid < 0:
        return +1
    return 0


def tau_prong_group_from_decaymode(dm):
    dm = int(dm)
    if dm in (0, 1, 2):
        return "prong1"
    if dm in (10, 11):
        return "prong23"
    if dm >= 10:
        return "prong23"
    return None


def tau_category(abs_eta, decay_mode):
    prong = tau_prong_group_from_decaymode(decay_mode)
    if prong == "prong1":
        if abs_eta < 0.8:
            return "prong1_eta0"
        if abs_eta < 1.5:
            return "prong1_eta1"
        if abs_eta < 2.4:
            return "prong1_eta2"
        return None
    if prong == "prong23":
        if abs_eta < 2.4:
            return "prong23_eta"
    return None


class EventNamespace(dict):
    def __init__(self, ev):
        super().__init__()
        self.ev = ev
        self["abs"] = abs
        self["max"] = max
        self["min"] = min
        self["pow"] = pow
        self["math"] = math

    def __missing__(self, key):
        val = getattr(self.ev, key)
        self[key] = val
        return val


def eval_weight(expr, ev):
    if expr is None or expr.strip() in ("", "1.0"):
        return 1.0
    ns = EventNamespace(ev)
    return float(eval(expr, {"__builtins__": {}}, ns))


def build_event_key(ev):
    return (int(ev.run), int(ev.luminosityBlock), int(ev.event))


def pass_tight_light_requirement(ev):
    return bool(getattr(ev, "Lepton2_isTight")) and bool(getattr(ev, "Lepton3_isTight"))


def pass_ossf_z(ev, z_window):
    pdg2 = int(getattr(ev, "Lepton2_pdgId"))
    pdg3 = int(getattr(ev, "Lepton3_pdgId"))
    if abs(pdg2) != abs(pdg3):
        return False
    if charge_from_pdgid(pdg2) * charge_from_pdgid(pdg3) >= 0:
        return False
    mll = (p4(ev, 2) + p4(ev, 3)).M()
    return abs(mll - Z_MASS) < z_window


def pass_frmode_event(ev, args):
    if abs(int(getattr(ev, "Lepton1_pdgId"))) != 15:
        return False
    if abs(int(getattr(ev, "Lepton2_pdgId"))) not in (11, 13):
        return False
    if abs(int(getattr(ev, "Lepton3_pdgId"))) not in (11, 13):
        return False
    if not bool(getattr(ev, "Lepton1_isFakeable")):
        return False
    if args.require_tight_light and not pass_tight_light_requirement(ev):
        return False
    if args.require_ossf_z and not pass_ossf_z(ev, args.z_window):
        return False
    if args.require_no_veto and int(getattr(ev, "nVetoLepton")) != 0:
        return False
    if args.min_goodjet >= 0 and int(getattr(ev, "nGoodJet")) < args.min_goodjet:
        return False
    if args.nbjet_eq >= 0 and int(getattr(ev, "nBjet")) != args.nbjet_eq:
        return False
    if args.goodleptoncode_abs is not None and abs(int(getattr(ev, "GoodLeptonCode"))) != args.goodleptoncode_abs:
        return False
    return True


def tau_inputs(ev):
    jet_pt = float(getattr(ev, "Lepton1_Jet_pt"))
    tau_pt = float(getattr(ev, "Lepton1_pt"))
    tau_eta = abs(float(getattr(ev, "Lepton1_eta")))
    decay_mode = int(getattr(ev, "Lepton1_tauDecayMode"))
    if jet_pt <= 0.0:
        jet_pt = tau_pt
    return jet_pt, tau_eta, decay_mode


def tau_is_prompt_genuine(ev):
    return int(getattr(ev, "Lepton1_tauGenPartFlav")) == 5


def load_yaml_file(path):
    with open(path) as f:
        return yaml.safe_load(f)


def derive_allowed_modes_from_grouping(grouping_path):
    path = Path(grouping_path)
    if not path.exists():
        return list(DEFAULT_ALLOWED_MODES)
    data = load_yaml_file(path)
    procs = data.get("processes", {}) if isinstance(data, dict) else {}
    modes = set()
    for _, info in procs.items():
        if not isinstance(info, dict):
            continue
        for mode in info.get("modes", []) or []:
            if isinstance(mode, str) and mode.startswith("FR"):
                modes.add(mode)
    return sorted(modes) if modes else list(DEFAULT_ALLOWED_MODES)


def _to_float_or_none(x):
    try:
        return float(x)
    except Exception:
        return None


def _find_scalar_case_insensitive(dct, candidates):
    if not isinstance(dct, dict):
        return None
    for k, v in dct.items():
        if str(k).lower() in {c.lower() for c in candidates}:
            val = _to_float_or_none(v)
            if val is not None:
                return val
    return None


def _find_map_case_insensitive(dct, candidates):
    if not isinstance(dct, dict):
        return None
    lower = {str(k).lower(): v for k, v in dct.items()}
    for cand in candidates:
        v = lower.get(cand.lower())
        if isinstance(v, dict):
            return v
    return None


def _collect_aliases(node, key_hint=None):
    aliases = []
    if key_hint:
        aliases.append(key_hint)
    if isinstance(node, dict):
        for k, v in node.items():
            if str(k).lower() in {x.lower() for x in DATASET_ALIAS_KEYS}:
                if isinstance(v, str):
                    aliases.append(v)
                elif isinstance(v, (list, tuple)):
                    aliases.extend([x for x in v if isinstance(x, str)])
    out = []
    seen = set()
    for alias in aliases:
        ca = canonical_dataset_name(alias)
        if ca and ca not in seen:
            seen.add(ca)
            out.append(ca)
    return out


def _merge_parallel_maps(node, out):
    if not isinstance(node, dict):
        return
    xmap = _find_map_case_insensitive(node, XSEC_KEYS)
    smap = _find_map_case_insensitive(node, SUMW_KEYS)
    if isinstance(xmap, dict) and isinstance(smap, dict):
        common = set(xmap.keys()) & set(smap.keys())
        for key in common:
            xsec = _to_float_or_none(xmap[key])
            sumw = _to_float_or_none(smap[key])
            ck = canonical_dataset_name(key)
            if ck and xsec is not None and sumw is not None:
                out[ck] = {"xsec": xsec, "sumw": sumw}


def flatten_xsec_entries(node, out, key_hint=None):
    if isinstance(node, dict):
        _merge_parallel_maps(node, out)
        xsec = _find_scalar_case_insensitive(node, XSEC_KEYS)
        sumw = _find_scalar_case_insensitive(node, SUMW_KEYS)
        if xsec is not None and sumw is not None:
            aliases = _collect_aliases(node, key_hint)
            if not aliases and key_hint:
                aliases = [canonical_dataset_name(key_hint)]
            for alias in aliases:
                if alias:
                    out[alias] = {"xsec": xsec, "sumw": sumw}
        for k, v in node.items():
            flatten_xsec_entries(v, out, k)
    elif isinstance(node, list):
        for item in node:
            flatten_xsec_entries(item, out, key_hint)


def build_dataset_norm_db(xsec_path, grouping_path=None):
    data = load_yaml_file(xsec_path)
    out = {}

    # Primary expected format in this analysis config:
    # crosssection: { DATASET: xsec }
    # Entries:      { DATASET: nEventsGenWeighted }
    if isinstance(data, dict):
        xmap = None
        smap = None
        for key, val in data.items():
            lk = str(key).lower()
            if lk in {k.lower() for k in XSEC_KEYS} and isinstance(val, dict):
                xmap = val
            if lk in {k.lower() for k in SUMW_KEYS} and isinstance(val, dict):
                smap = val
        if isinstance(xmap, dict) and isinstance(smap, dict):
            for raw_key, xsec_val in xmap.items():
                short = canonical_dataset_name(raw_key)
                xsec = _to_float_or_none(xsec_val)
                sumw = _to_float_or_none(smap.get(raw_key))
                if short and xsec is not None and sumw is not None:
                    out[short] = {"xsec": xsec, "sumw": sumw}

    # Fallback generic recursive parser
    if not out:
        flatten_xsec_entries(data, out)

    # Add aliases from grouping.yaml such as MC2017.TTZToLLNuNu -> TTZToLLNuNu
    if grouping_path is not None and Path(grouping_path).exists():
        gdata = load_yaml_file(grouping_path)
        procs = gdata.get("processes", {}) if isinstance(gdata, dict) else {}
        for _, info in procs.items():
            if not isinstance(info, dict):
                continue
            for ds in info.get("datasets", []) or []:
                if not isinstance(ds, str):
                    continue
                if ds.startswith("MC2017."):
                    short = canonical_dataset_name(ds.split(".", 1)[1])
                    if short in out:
                        out[canonical_dataset_name(ds)] = out[short]

    return out


def read_sumw_from_dataset_files(dataset_files):
    total = 0.0
    for fpath in dataset_files:
        tf = ROOT.TFile.Open(fpath)
        if not tf or tf.IsZombie():
            continue
        hist = tf.Get("nEventsGenWeighted")
        if hist:
            try:
                total += float(hist.GetBinContent(1))
            except Exception:
                pass
        tf.Close()
    return total


def build_dataset_file_index(files):
    out = {}
    for f in files:
        full_ds = dataset_dir_from_file(f)
        short_ds = dataset_short_name(full_ds)
        for ds in (full_ds, short_ds):
            if ds is not None:
                out.setdefault(ds, []).append(f)
    return out


def find_dataset_norm(dataset_name, norm_db):
    ds_full = canonical_dataset_name(dataset_name)
    ds_short = dataset_short_name(dataset_name)
    if ds_full is None:
        return None

    candidates = []
    for cand in (ds_full, ds_short):
        if cand and cand not in candidates:
            candidates.append(cand)

    # tolerant matching: long directory names often start with the short dataset key
    for key in norm_db.keys():
        if key in candidates:
            return norm_db[key]
        if ds_full.startswith(key) or key.startswith(ds_full):
            candidates.append(key)
        elif ds_short and (ds_short.startswith(key) or key.startswith(ds_short)):
            candidates.append(key)

    seen = set()
    for cand in candidates:
        if cand in seen:
            continue
        seen.add(cand)
        if cand in norm_db:
            return norm_db[cand]
    return None


def current_file_name(chain):
    f = chain.GetCurrentFile()
    return f.GetName() if f else ""


def is_npl_path(file_name):
    return "/NPL" in file_name or Path(file_name).parts[-3].startswith("NPL") if file_name else False


def select_mc_weight_expr(file_name, args):
    return args.nplmc_weight if is_npl_path(file_name) else args.mc_weight


def compute_dataset_scale_factor(dataset_name, args, norm_db, dataset_file_index, cache):
    ds_full = canonical_dataset_name(dataset_name)
    ds_short = dataset_short_name(dataset_name)
    cache_key = ds_short or ds_full
    if cache_key in cache:
        return cache[cache_key]
    entry = find_dataset_norm(ds_full, norm_db)
    if entry is None:
        raise KeyError(
            f"Dataset '{dataset_name}' not found in crosssection yaml. "
            f"Please check naming in {args.crosssection}."
        )
    xsec = float(entry["xsec"])
    sumw = float(entry["sumw"])
    if sumw == 0.0:
        sumw = read_sumw_from_dataset_files(dataset_file_index.get(ds_short, []) or dataset_file_index.get(ds_full, []))
    if sumw == 0.0:
        raise ZeroDivisionError(f"Dataset '{dataset_name}' has zero nEventsGenWeighted.")
    scale = args.lumi_fb * 1000.0 * xsec / sumw
    cache[cache_key] = scale
    return scale


def fill_chain(chain, args, is_data, h_denom, h_numer, norm_db=None, dataset_file_index=None):
    nentries = chain.GetEntries()
    seen_data = set()
    kept_events = 0
    kept_unique_data = 0
    last_dataset = None
    last_expr = None
    last_scale = None
    scale_cache = {}

    for iev, ev in enumerate(chain):
        file_name = current_file_name(chain)

        if not pass_frmode_event(ev, args):
            continue

        if is_data and args.dedup_data:
            key = build_event_key(ev)
            if key in seen_data:
                continue
            seen_data.add(key)
            kept_unique_data += 1

        jet_pt, abs_eta, decay_mode = tau_inputs(ev)
        cat = tau_category(abs_eta, decay_mode)
        if cat is None:
            continue

        kept_events += 1

        if is_data:
            w = 1.0
        else:
            if not tau_is_prompt_genuine(ev):
                continue
            dataset_name = dataset_dir_from_file(file_name)
            weight_expr = select_mc_weight_expr(file_name, args)
            dataset_scale = compute_dataset_scale_factor(dataset_name, args, norm_db, dataset_file_index, scale_cache)
            if dataset_name != last_dataset or weight_expr != last_expr or dataset_scale != last_scale:
                print(f"[INFO] switched MC normalization for dataset: {dataset_name}")
                print(f"[INFO]   -> using weight expr : {weight_expr}")
                print(f"[INFO]   -> using scale factor: {dataset_scale:.12g}")
                last_dataset = dataset_name
                last_expr = weight_expr
                last_scale = dataset_scale
            w = dataset_scale * eval_weight(weight_expr, ev)

        h_denom[cat].Fill(jet_pt, w)
        if bool(getattr(ev, "Lepton1_isTight")):
            h_numer[cat].Fill(jet_pt, w)

        if (iev + 1) % 200000 == 0:
            print(f"[INFO] processed {iev+1} / {nentries}")

    return {
        "kept_events": kept_events,
        "unique_data_events": kept_unique_data if is_data and args.dedup_data else None,
    }


def build_fr_hist(h_num_data, h_den_data, h_num_mc, h_den_mc, out_name):
    h_fr = h_den_data.Clone(out_name)
    h_fr.Reset("ICES")

    h_num_sub = h_num_data.Clone(out_name + "_numSub")
    h_den_sub = h_den_data.Clone(out_name + "_denSub")
    h_num_sub.Add(h_num_mc, -1.0)
    h_den_sub.Add(h_den_mc, -1.0)

    for ib in range(1, h_fr.GetNbinsX() + 1):
        num = h_num_sub.GetBinContent(ib)
        den = h_den_sub.GetBinContent(ib)
        err_num = h_num_sub.GetBinError(ib)
        err_den = h_den_sub.GetBinError(ib)

        if den <= 0.0:
            h_fr.SetBinContent(ib, 0.0)
            h_fr.SetBinError(ib, 0.0)
            continue

        fr = num / den
        err = math.sqrt((err_num / den) ** 2 + ((num * err_den) / (den * den)) ** 2)
        h_fr.SetBinContent(ib, fr)
        h_fr.SetBinError(ib, err)

    return h_fr, h_num_sub, h_den_sub


def print_table(h):
    print(f"\n[{h.GetName()}]")

    for ib in range(1, h.GetNbinsX() + 1):
        xlow = h.GetXaxis().GetBinLowEdge(ib)
        xup = h.GetXaxis().GetBinUpEdge(ib)
        val = h.GetBinContent(ib)
        err = h.GetBinError(ib)
        print(f"  {xlow:6.1f} - {xup:6.1f} GeV : {val:.6f} +/- {err:.6f}")


def main():
    parser = argparse.ArgumentParser(
        description="Measure tau fake rate from FR one-tau trilepton ntuples (FRTaElEl/FRTaMuMu)."
    )
    parser.add_argument("--data-list", required=True, help="txt file with data ROOT paths")
    parser.add_argument("--mc-list", required=True, help="txt file with MC ROOT paths")
    parser.add_argument("--tree", default="Events", help="tree name")
    parser.add_argument("--out", default="fr_tau_2017_frmode.root", help="output ROOT file")
    parser.add_argument("--mc-weight", default=DEFAULT_MC_WEIGHT, help="MC nominal weight expression")
    parser.add_argument("--nplmc-weight", default=DEFAULT_NPLMC_WEIGHT, help="NPL-mode MC nominal weight expression")
    parser.add_argument("--grouping", default=DEFAULT_GROUPING_PATH, help="path to grouping.yaml")
    parser.add_argument("--crosssection", default=DEFAULT_XSEC_PATH, help="path to crosssection.yaml")
    parser.add_argument("--lumi-fb", type=float, default=DEFAULT_LUMI_FB, help="integrated luminosity in fb^-1")
    parser.add_argument("--z-window", type=float, default=15.0, help="|mll-mZ| < z_window")
    parser.add_argument("--min-goodjet", type=int, default=-1, help="minimum nGoodJet; -1 disables")
    parser.add_argument("--nbjet-eq", type=int, default=0, help="exact nBjet for MR; -1 disables")
    parser.add_argument("--require-ossf-z", action="store_true", default=True,
                        help="require OSSF light-lepton pair near Z (default: on)")
    parser.add_argument("--require-tight-light", action="store_true", default=True,
                        help="require both light leptons to pass tight selection (default: on)")
    parser.add_argument("--require-no-veto", action="store_true", default=False,
                        help="require nVetoLepton == 0")
    parser.add_argument("--goodleptoncode-abs", type=int, default=None,
                        help="optionally require abs(GoodLeptonCode) == value")
    parser.add_argument("--dedup-data", action="store_true", default=True,
                        help="deduplicate data by (run,lumi,event) across PDs (default: on)")
    parser.add_argument("--fail-on-negative-subtraction", action="store_true", default=False,
                        help="exit with an error if any bin has negative subtracted numerator or denominator")
    args = parser.parse_args()

    allowed_modes = derive_allowed_modes_from_grouping(args.grouping)
    data_files_all = read_file_list(args.data_list)
    mc_files_all = read_file_list(args.mc_list)
    data_files = filter_files_by_mode(data_files_all, allowed_modes)
    mc_files = filter_files_by_mode(mc_files_all, allowed_modes)

    dataset_norm_db = build_dataset_norm_db(args.crosssection, args.grouping)
    dataset_file_index = build_dataset_file_index(mc_files)

    print("[INFO] allowed FR modes    =", ",".join(allowed_modes))
    print("[INFO] grouping path       =", args.grouping)
    print("[INFO] crosssection path   =", args.crosssection)
    print("[INFO] lumi [fb^-1]        =", args.lumi_fb)
    print("[INFO] norm datasets found =", len(dataset_norm_db))
    print("[INFO] input data files    =", len(data_files_all))
    print("[INFO] kept data files     =", len(data_files))
    print("[INFO] input mc files      =", len(mc_files_all))
    print("[INFO] kept mc files       =", len(mc_files))

    ch_data = build_chain(args.tree, data_files)
    ch_mc = build_chain(args.tree, mc_files)

    print("[INFO] data entries =", ch_data.GetEntries())
    print("[INFO] mc   entries =", ch_mc.GetEntries())
    print("[INFO] nominal mc weight =", args.mc_weight)
    print("[INFO] NPL mc weight     =", args.nplmc_weight)
    print("[INFO] nbjet_eq          =", args.nbjet_eq)
    print("[INFO] min_goodjet       =", args.min_goodjet)
    print("[INFO] z_window          =", args.z_window)

    h_den_data = make_result_hists("den_data")
    h_num_data = make_result_hists("num_data")
    h_den_mc = make_result_hists("den_promptTau_mc")
    h_num_mc = make_result_hists("num_promptTau_mc")

    print("[INFO] looping over data")
    data_stats = fill_chain(ch_data, args, True, h_den_data, h_num_data)
    print("[INFO] data kept events   =", data_stats["kept_events"])
    if data_stats["unique_data_events"] is not None:
        print("[INFO] unique data events=", data_stats["unique_data_events"])

    print("[INFO] looping over MC")
    mc_stats = fill_chain(ch_mc, args, False, h_den_mc, h_num_mc, dataset_norm_db, dataset_file_index)
    print("[INFO] mc kept events     =", mc_stats["kept_events"])

    fout = ROOT.TFile.Open(args.out, "RECREATE")

    for cat_name, _, _, _ in CATEGORIES:
        print(f"\n[DEBUG] {cat_name}")

        print("  den_data integral      =", h_den_data[cat_name].Integral())
        print("  num_data integral      =", h_num_data[cat_name].Integral())
        print("  den_promptTau_mc int   =", h_den_mc[cat_name].Integral())
        print("  num_promptTau_mc int   =", h_num_mc[cat_name].Integral())

        h_fr, h_num_sub, h_den_sub = build_fr_hist(
            h_num_data[cat_name],
            h_den_data[cat_name],
            h_num_mc[cat_name],
            h_den_mc[cat_name],
            f"FR_tau_{cat_name}"
        )

        min_num_sub = min(h_num_sub.GetBinContent(i) for i in range(1, h_num_sub.GetNbinsX() + 1))
        min_den_sub = min(h_den_sub.GetBinContent(i) for i in range(1, h_den_sub.GetNbinsX() + 1))
        print("  min(num_sub)           =", min_num_sub)
        print("  min(den_sub)           =", min_den_sub)

        if args.fail_on_negative_subtraction and (min_num_sub < 0.0 or min_den_sub < 0.0):
            raise RuntimeError(
                f"Negative subtracted yield found in {cat_name}. "
                "The chosen measurement region is prompt-dominated and not suitable for FR measurement."
            )

        for h in (
            h_den_data[cat_name], h_num_data[cat_name],
            h_den_mc[cat_name], h_num_mc[cat_name],
            h_num_sub, h_den_sub, h_fr
        ):
            h.Write()

        print_table(h_fr)

    fout.Close()
    print(f"[INFO] wrote {args.out}")


if __name__ == "__main__":
    main()
