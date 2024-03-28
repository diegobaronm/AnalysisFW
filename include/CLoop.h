//////////////////////////////////////////////////////////
// This class has been automatically generated on
// Tue Dec 10 15:57:16 2019 by ROOT version 6.18/04
// from TTree NOMINAL/NOMINAL
// found on file: user.sdysch.19616269._000010.LepUniv_ttbar.root
//////////////////////////////////////////////////////////

#ifndef CLoop_h
#define CLoop_h

#include <TROOT.h>
#include <TChain.h>
#include <TFile.h>
#include <TH1.h>
#include <TH2.h>
#include <TStyle.h>
#include <TCanvas.h>
#include <iostream>
#include <vector>
#include <time.h>
#include <math.h>
#include <memory>
#include "HistogramContainer.h"
#include "VBFBDT.h"
#include "OutputTree.h"

// Header file for the classes stored in the TTree if any.
#include <TLorentzVector.h>


class CLoop {
   public :
   void Style(double lumFactor);
   void ActivateBranches(const std::string& key);
   void Fill(double weight, int z_sample, const std::string& sampleName);
   void FillTree(double weight, int z_sample, const std::string& sampleName);
   void createOutputFile(const std::string& key);
   CLoop(TTree *tree=0,std::string sample_name="");
   ~CLoop();
   Int_t    Cut(/*Long64_t entry*/);
   Int_t    GetEntry(Long64_t entry);
   Long64_t LoadTree(Long64_t entry);
   void     Init(TTree *tree,std::string sample_name="");
   void     Loop(double lumFactor, int z_sample, std::string key);
   Bool_t   Notify();
   void     Show(Long64_t entry = -1);

   private:
   TTree          *fChain;   //!pointer to the analyzed TTree or TChain
   Int_t           fCurrent; //!current Tree number in a TChain
   // Output file where all the info is going to be written. 
   // NOTE : The order here is VERY important. The unique_ptr must be declared first.
   std::unique_ptr<TFile> m_outputFile;
   // Declare the branches of the tree
   #include "DeclareTreeBranches.h"
   // Declare the histograms
   #include "DeclareHistograms.h"
   VBFBDT m_vbfBDT;
   // Output trees
   OutputTree m_signalTree{"SIGNAL", "Signal TTree"};
   OutputTree m_backgroundTree{"BG", "Background TTree"};
};

#endif



