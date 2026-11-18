#ifndef PhysicsTools_NanoAODTools_JetPUIDSFCorrector_h
#define PhysicsTools_NanoAODTools_JetPUIDSFCorrector_h

#include <iostream>
#include <string>
#include <vector>
#include <TH2.h>
#include <TFile.h>
#include <cmath>

#include "TZWi/TopAnalysis/interface/WeightCalculatorFromHistogram.h"

class JetPUIDSFCorrector {
 public:

  JetPUIDSFCorrector() {effmaps_.clear();}
  JetPUIDSFCorrector(std::vector<std::string> files, std::vector<std::string> histos);
  ~JetPUIDSFCorrector() {}

  void setLeptons(int nLep, int *lepPdgId, float *lepPt, float *lepEta);

  float getJPUIDSF(float pt, float eta);
  
private:
  std::vector<TH2F*> effmaps_;
  std::vector<float> ret_;
  int nLep_;
  float *Lep_eta_, *Lep_pt_;
  int *Lep_pdgId_;
};

#endif
