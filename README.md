# FCNC UL Run 2 Tau Fake Rate

Required release: CMSSW_13_3_3.

Branches: 20UL16APV, 20UL16, 20UL17, 20UL18.

From an empty CMSSW_13_3_3/src directory, run:

    git clone -b 20UL18 --single-branch https://github.com/panthera718/FCNC_20ULRun2_TauFakeRate.git .

## Measuring the tau fake rate

This workflow measures the tau fake rate (FR) in events containing a tau candidate and either an electron pair or a muon pair. The example below shows how to produce the 2018 measurement ntuples, calculate the fake rates and their uncertainties, and apply them in `FCNC_20ULRun2_Variation`.

### 1. Produce the measurement ntuples

Use the skims produced by [`FCNC_withtau_20ULRun2_RemakeNANOAOD`](https://github.com/panthera718/FCNC_withtau_20ULRun2_RemakeNANOAOD) as input. For 2018, use the `20UL18` branch of this repository in the `CMSSW_13_3_3` environment set up above.

The 2018 event flags and HLT configuration are the same as those in the `20UL18_central` branch of `FCNC_20ULRun2_Variation`. The fake-rate measurement uses two dedicated channels, `FRTaElEl` for a tau candidate and two electrons, and `FRTaMuMu` for a tau candidate and two muons.

Update the per-dataset `.txt` files under `TZWi/TopAnalysis/data/datasets/NanoAOD/2018` to point to your Remake skims. With the CMSSW environment active and `create-batch3_mine` available, submit both channels using the [2018 submission script](https://github.com/panthera718/FCNC_20ULRun2_TauFakeRate/blob/20UL18/TZWi/TopAnalysis/test/fcncTriLepton/01.1_submit.py).

```bash
cd "$CMSSW_BASE/src/TZWi/TopAnalysis/test/fcncTriLepton"
python3 01.1_submit.py
```

### 2. Prepare the data and MC file lists

Once the batch jobs finish, collect the output files under `ntuple_2018/reco/<channel>/<dataset>/<file>.root`. The measurement reads two file lists from `TZWi/TopAnalysis/data/tauFR`, with one ROOT file path per line.

| File list | Contents |
| --- | --- |
| `data_2018_tauFR.txt` | Measurement ntuples from collision data |
| `mc_2018_tauFR.txt` | Measurement ntuples from simulation |

The supplied lists use the following relative paths:

```text
ntuple_2018_onetau/reco/FRTaElEl/<dataset>/<file>.root
ntuple_2018_onetau/reco/FRTaMuMu/<dataset>/<file>.root
```

If your dataset and file names match the supplied lists and you extracted `ntuple_2018` under `submit_2018/`, create this symbolic link:

```bash
cd "$CMSSW_BASE/src/TZWi/TopAnalysis/data/tauFR"
ln -sT ../../test/fcncTriLepton/submit_2018/ntuple_2018 ntuple_2018_onetau
```

If you stored `ntuple_2018` elsewhere, use its absolute path as the link target. If your production generated different file names, update both lists with the actual ROOT file paths. Preserve the `<channel>/<dataset>/<file>.root` structure. The measurement script selects channels using `/FRTaElEl/` or `/FRTaMuMu/` in the path and uses the immediate parent directory of each MC file to look up its dataset normalization.

### 3. Measure the tau fake rate in the five application bins

The [measurement script](https://github.com/panthera718/FCNC_20ULRun2_TauFakeRate/blob/20UL18/TZWi/TopAnalysis/data/tauFR/measure_fr_tau_frmode.py) uses eight bins by default. Before running it, set `PT_BINS` to the five-bin configuration used by `TAU_FR` in `FCNC_20ULRun2_Variation`:

```python
PT_BINS = [20.0, 30.0, 40.0, 50.0, 100.0, 300.0]
```

These bin edges apply to the transverse momentum ($p_T$) of the jet matched to the tau candidate, in GeV. If the matched jet has $p_T \leq 0$, the script uses the tau candidate's $p_T$. The candidate selection during ntuple production has a separate threshold. For 2018, TauFakeRate requires the tau candidate to have $p_T > 15$ GeV, while the central Variation analysis requires $p_T > 20$ GeV.

Run the measurement in a CMSSW environment with PyROOT and PyYAML available:

```bash
cd "$CMSSW_BASE/src/TZWi/TopAnalysis/data/tauFR"
python3 measure_fr_tau_frmode.py \
  --data-list data_2018_tauFR.txt \
  --mc-list mc_2018_tauFR.txt \
  --out fr_tau_2018_remeasured.root
```

The script reads `config/grouping.yaml` and `config/crosssection.yaml` from the working directory. Check `kept data files`, `kept mc files`, `data entries`, and `mc entries` in the log to confirm that both inputs were read.

The default 2018 configuration uses an integrated luminosity of 59.8 fb⁻¹. It requires a tight, opposite-sign electron or muon pair of the same flavor, with $|m_{\ell\ell} - 91.2\,\mathrm{GeV}| < 15\,\mathrm{GeV}$, and zero b-tagged jets (`nBjet == 0`). In each bin, the numerator counts tight tau candidates in data and the denominator counts fakeable tau candidates in data. The script subtracts the corresponding genuine-tau MC contribution from each count before taking their ratio.

### 4. Apply the new fake rates in `FakeRateProducer.py`

For 2018, open [`FakeRateProducer.py` on the `20UL18_central` branch](https://github.com/panthera718/FCNC_20ULRun2_Variation/blob/20UL18_central/TZWi/TopAnalysis/python/postprocessing/FakeRateProducer.py). Use the histograms in `fr_tau_2018_remeasured.root` to update `FakeRateProducer.TAU_FR["2018"]` as follows:

| Measurement histogram | Keys under `TAU_FR["2018"]` |
| --- | --- |
| `FR_tau_prong1_eta0` | `["prong1"]["absEta_0p0_0p8"]` |
| `FR_tau_prong1_eta1` | `["prong1"]["absEta_0p8_1p5"]` |
| `FR_tau_prong1_eta2` | `["prong1"]["absEta_1p5_2p4"]` |
| `FR_tau_prong23_eta` | `["prong23"]["absEta_0p0_2p4"]` |

For each histogram, read ROOT bins `1` through `5`. Fill the `fr` array with `GetBinContent(i)` and the `err` array with `GetBinError(i)`, in increasing $p_T$ order: 20–30, 30–40, 40–50, 50–100, and 100–300 GeV. The script also prints the value and uncertainty for each bin at the end of the run.

For other eras, repeat the measurement using the data and MC file lists and normalization settings from the corresponding measurement branch. Update the era key on the matching Variation branch.

| Measurement branch | Variation branch | `TAU_FR` era key |
| --- | --- | --- |
| `20UL16APV` | `20UL16APV_central` | `"2016preVFP"` |
| `20UL16` | `20UL16_central` | `"2016postVFP"` |
| `20UL17` | `20UL17_central` | `"2017"` |
| `20UL18` | `20UL18_central` | `"2018"` |
