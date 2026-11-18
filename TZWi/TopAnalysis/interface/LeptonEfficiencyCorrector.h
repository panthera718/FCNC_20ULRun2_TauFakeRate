#ifndef PhysicsTools_NanoAODTools_LeptonEfficiencyCorrector_h
#define PhysicsTools_NanoAODTools_LeptonEfficiencyCorrector_h

#include <iostream>
#include <string>
#include <vector>
#include <TH2.h>
#include <TFile.h>
#include <cmath>

#include "TZWi/TopAnalysis/interface/WeightCalculatorFromHistogram.h"

class LeptonEfficiencyCorrector {
 public:

  LeptonEfficiencyCorrector() {effmaps_.clear();}
  LeptonEfficiencyCorrector(std::vector<std::string> files, std::vector<std::string> histos);
  ~LeptonEfficiencyCorrector() {}

  void setLeptons(int nLep, int *lepPdgId, float *lepPt, float *lepEta);

  float getSF(int pdgid, float pt, float eta);
  float getTrigSF(float lep1_pt, float lep2_pt);
  float getSFErr(int pdgid, float pt, float eta);
  float getTrigSFErr(float lep1_pt, float lep2_pt);
  const std::vector<float> & run();

private:
  std::vector<TH2F*> effmaps_;
  std::vector<float> ret_;
  int nLep_;
  float *Lep_eta_, *Lep_pt_;
  int *Lep_pdgId_;
};

#endif