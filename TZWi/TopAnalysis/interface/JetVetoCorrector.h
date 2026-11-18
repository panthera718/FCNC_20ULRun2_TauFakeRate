#ifndef PhysicsTools_NanoAODTools_JetVetoCorrector_h
#define PhysicsTools_NanoAODTools_JetVetoCorrector_h

#include <iostream>
#include <string>
#include <vector>
#include <TH2.h>
#include <TFile.h>
#include <cmath>

#include "TZWi/TopAnalysis/interface/WeightCalculatorFromHistogram.h"

class JetVetoCorrector {
 public:

  JetVetoCorrector() {effmaps_.clear();}
  JetVetoCorrector(std::vector<std::string> files, std::vector<std::string> histos);
  ~JetVetoCorrector() {}

  void setLeptons(int nLep, int *lepPdgId, float *lepPt, float *lepEta);

  float getJV(float eta, float phi);
  
private:
  std::vector<TH2F*> effmaps_;
  std::vector<float> ret_;
  int nLep_;
  float *Lep_eta_, *Lep_pt_;
  int *Lep_pdgId_;
};

#endif
