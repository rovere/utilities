#include "TH1F.h"
#include "TH2F.h"
#include "TFile.h"
#include "RooRealVar.h"
#include "RooGaussian.h"
#include "RooDataSet.h"
#include <set>
#include <iostream>
#include <stdio.h>

void format_title(char * title, size_t size, const char * prefix, int pu, float sigma) {
  snprintf(title, size, "%s_PU%d_SIGMA%4.2f", prefix, pu, sigma);
}

void bs(int experiments=100, int pu_min=2, int pu_max=70, float sigma_value_min=3.0, float sigma_value_max=5.0) {
  std::vector<TH1F *> dists;
  std::vector<TH1F *> abs_dists;
  std::vector<TH1F *> abs_min_dists;
  std::vector<TH1F *> ave_mergeds;
  float sigma_step = 0.1; // cm
  int number_of_histograms = (int)((pu_max-pu_min)*(sigma_value_max-sigma_value_min)/sigma_step);
  char filename[100];
  snprintf(filename, sizeof(filename),
           "bs_PUmin%d_PUMax%d_SigmaMin%4.2f_SigmaMax%4.2f.root",
           pu_min, pu_max, sigma_value_min, sigma_value_max);
  TFile output(filename, "RECREATE");
  TH2F * density_pu_sigma = new TH2F("Average PU_density at origin",
                                     "Average PU_density at origin",
                                     (pu_max-pu_min),
                                     pu_min, pu_max,
                                     (int)((sigma_value_max-sigma_value_min)/sigma_step)+1,
                                     sigma_value_min, sigma_value_max);
  TH2F * ave_merge_rate_pu_sigma = new TH2F("Average merge-rate",
                                            "Average merge-rate",
                                            (pu_max-pu_min),
                                            pu_min, pu_max,
                                            (int)((sigma_value_max-sigma_value_min)/sigma_step)+1,
                                            sigma_value_min, sigma_value_max);
  TH2F * two_vertices_mean_closest_distance_pu_sigma = new TH2F("Two Vertices Mean Closest Distance",
                                                                "Two Vertices Mean Closest Distance",
                                                                (pu_max-pu_min),
                                                                pu_min, pu_max,
                                                                (int)((sigma_value_max-sigma_value_min)/sigma_step)+1,
                                                                sigma_value_min, sigma_value_max);

  // The probability should be mostly independent of the pileup: the
  // distribution of the differences in z among pairs of vertices is
  // still distrubuted with a gaussion with sqrt(2)*sigma_z, hence the
  // probability, which is calculated using CDF of this distribution,
  // should reflect this independece, and indeed it does. This is true
  // only in an ideal world, of course, where all vertices are
  // reconstructed, irrespectively of their relative distance. In a
  // realistic sample, this measure will be affected by efficiency and
  // merge rate.
  TH2F * prob_two_vertices_closer_1mm_pu_sigma = new TH2F("prob_two_vertices_closer_1mm",
                                                          "prob_two_vertices_closer_1mm",
                                                          (pu_max-pu_min),
                                                          pu_min, pu_max,
                                                          (int)((sigma_value_max-sigma_value_min)/sigma_step)+1,
                                                          sigma_value_min, sigma_value_max);
  dists.reserve(number_of_histograms);
  abs_dists.reserve(number_of_histograms);
  abs_min_dists.reserve(number_of_histograms);
  ave_mergeds.reserve(number_of_histograms);
  float merge_distance = 0.05; // in cm, 500u the merge rate is ~20%
  float merge_rate_at_merge_distance = 0.2; // in percentage, it's 20% at 500 microns
  char title[20];
  for (int pu = pu_min; pu <= pu_max; ++pu) {
    for (float sigma_value = sigma_value_min;
         sigma_value <= sigma_value_max;
         sigma_value += sigma_step) {

      // Distances of all vertices w.r.t all others, counted only once.
      format_title(title, sizeof(title), "d", pu, sigma_value);
      dists.push_back( new TH1F(title, title, 8000, -40, 40)); // 100u bins

      // Absolute distance of all vertices w.r.t all others, counted only once.
      format_title(title, sizeof(title), "ad", pu, sigma_value);
      abs_dists.push_back( new TH1F(title, title, 4000, 0, 40)); // 100u bins

      // Absolute minimum distance for all vertices w.r.t all others,
      // counted only once. This represents the minimum of all the
      // distances computed among all possible pairs of vertices. The
      // plot is filled in such a way that overflow entries are put in
      // the last available bin, so that the mean is correctly
      // computed.
      format_title(title, sizeof(title), "amd", pu, sigma_value);
      abs_min_dists.push_back( new TH1F(title, title, 4000, 0, 0.4)); // 4mm/4000 = 1u/bin

      // Number of vertices whose distance is closer than 500u,
      // counted only once.
      format_title(title, sizeof(title), "avm", pu, sigma_value);
      ave_mergeds.push_back( new TH1F(title, title, pu, 0, pu));
 
      TH1F * dist = dists.back();
      TH1F * abs_dist = abs_dists.back();
      TH1F * abs_min_dist = abs_min_dists.back();
      TH1F * ave_merged = ave_mergeds.back();
      float NPU = pu;
      int events = max(NPU*experiments,100000/NPU);
      RooRealVar z("z", "z", 0, -20, 20);
      RooRealVar sigma("sigma", "sigma", sigma_value);
      RooRealVar mean("mean", "mean", 0);
      RooGaussian bsz("bsz", "bsz", z, mean, sigma);
      RooDataSet * data = bsz.generate(z, events);
      std::set<int> merged;
      for (int i = 0; i <= events - NPU ; i +=NPU) {
        float minimum = 9999;
        for (int j = i; j < i + NPU; ++j) {
          for (int k = j + 1; k < i + NPU; ++k) {
            //        std::cout << i << ", " << j << ", " << k << std::endl;
            float d = data->get(j)->getRealValue("z") - data->get(k)->getRealValue("z");
            if (abs(d) < minimum)
              minimum = abs(d);
            dist->Fill(d);
            abs_dist->Fill(abs(d));
            if (abs(d) < merge_distance) {
              //          std::cout << j << ", " << k << ", " << d << std::endl;
              merged.insert(j);
              merged.insert(k);
            }
          }
        } // end of loop over 1 single experiment with NPU events
        //    std::cout << minimum << std::endl;
        abs_min_dist->Fill((minimum < abs_min_dist->GetXaxis()->GetXmax())
                           ? minimum : abs_min_dist->GetXaxis()->GetXmax());
        ave_merged->Fill(merged.size());
        merged.clear(); // reset merged vertices for the next experiment
      } // End of loop over all the experiments at the same PU/Sigma.
      density_pu_sigma->Fill(pu, sigma_value, pu*bsz.getVal(z=0));
      ave_merge_rate_pu_sigma->Fill(pu, sigma_value, ave_merged->GetMean()*merge_rate_at_merge_distance/(float)pu);
      two_vertices_mean_closest_distance_pu_sigma->Fill(pu, sigma_value, abs_min_dist->GetMean());
      TH1F * c = (TH1F*)abs_dist->GetCumulative();
      c->Scale(1/abs_dist->GetEntries());
      prob_two_vertices_closer_1mm_pu_sigma->Fill(pu, sigma_value, c->GetBinContent(c->GetXaxis()->FindBin(0.1)));
      std::cout << "PU=" << pu << ", Sigma=" << sigma_value;
      std::cout << " Av.Merged=" << ave_merged->GetMean() << " Eff.Merged=" << ave_merged->GetMean()*merge_rate_at_merge_distance;
      //  std::cout << abs_dist->Integral(0,1) << std::endl;
      std::cout << " " << pu*bsz.getVal(z=0) << " [PU/cm] " << abs_min_dist->GetMean()*10 << " " << abs_dist->GetMean()*10 << " [mm]" << std::endl;
    } // End of loop over different sigmas
  } // End of loop over different PU
  density_pu_sigma->Write();
  ave_merge_rate_pu_sigma->Write();
  two_vertices_mean_closest_distance_pu_sigma->Write();
  prob_two_vertices_closer_1mm_pu_sigma->Write();
  for( auto j : dists)
    j->Write();
  for (auto j : abs_dists)
    j->Write();
  for (auto j : abs_min_dists)
    j->Write();
  for (auto j : ave_mergeds)
    j->Write();
}
