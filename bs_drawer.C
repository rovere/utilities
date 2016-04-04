#include "TColor.h"
#include "TFile.h"
#include "TROOT.h"
#include "TStyle.h"
#include "TObjArray.h"
#include "TH2F.h"
#include "TCanvas.h"
#include "TText.h"
#include "TMarker.h"

#include <iostream>
#include <vector>

void fill_gradient(const TColor & first,
                   const TColor & last,
                   const std::vector<float> &levels,
                   float threshold,
                   std::vector<int> &gradient,
                   unsigned int index=0)
{
  if (index == 0) {
    // if no index was given, find the highest used one and start from that plus one
    index = ((TObjArray*) gROOT->GetListOfColors())->GetLast() + 1;
  }

  int steps = levels.size();
  assert(steps > 1);
  bool assigned = false;
  float step_size = levels[1] - levels[0];
  float r1, g1, b1, r2, g2, b2;
  first.GetRGB(r1, g1, b1);
  last.GetRGB(r2, g2, b2);
  float delta_r = (r2 - r1) / (steps - 1);
  float delta_g = (g2 - g1) / (steps - 1);
  float delta_b = (b2 - b1) / (steps - 1);
  
  gradient.resize(steps);
  for (int i = 0; i < steps; ++i) {
    //    std::cout << i << " " << levels[i] << " " << threshold << std::endl;
    if (!assigned && abs(levels[i] - threshold) < step_size ) {
      assigned = true;
      gradient[i] = kRed;
      std::cout << "Setting special color at threshold " << levels[i] << std::endl;
    } else {
      new TColor(static_cast<Int_t>(index + i), r1 + delta_r * i, g1 + delta_g * i, b1 + delta_b * i);
      gradient[i] = index + i;
    }
  }
}

void fill_gradient(unsigned int first,
                   unsigned int last,
                   const std::vector<float> &levels,
                   float threshold,
                   std::vector<int> &gradient,
                   unsigned int index=0) {
  fill_gradient(* (TColor *) gROOT->GetListOfColors()->At(first),
                * (TColor *) gROOT->GetListOfColors()->At(last),
                levels, threshold, gradient);
}

void DrawTextAndMarker(float x,
                       float y,
                       int marker,
                       const char * text,
                       TText ** t,
                       TMarker ** m) {
  (*t) = new TText(x, y, text);
  (*m) = new TMarker(x, y, marker);
  (*t)->SetTextFont(43);
  (*t)->SetTextSize(20);
  (*t)->SetTextAlign(12);
  (*t)->Draw();
  (*m)->Draw();
}

void bs_drawer(const char * filename,
               const char * histo,
               float minimum,
               float maximum,
               int steps,
               float threshold,
               EColor start_palette=kBlue,
               EColor end_palette=kYellow)
{
  std::vector<float> levels;
  std::vector<int> colors;
  levels.reserve(steps);
  colors.reserve(steps);
  float increment = (maximum - minimum)/(float)steps;
  for (float j = minimum; j <= maximum; j += increment)
    levels.push_back(j);

  fill_gradient(start_palette, end_palette,
                levels, threshold, colors);
  TFile * f = new TFile(filename);
  TH2F * h = (TH2F*)f->Get(histo);
  gStyle->SetPalette(colors.size(), &colors.front() );
  std::cout << colors.size() << std::endl;
  gStyle->SetNumberContours(colors.size());
  gStyle->SetOptStat(0);
  h->SetMinimum(minimum);
  h->SetMaximum(maximum);
  h->GetXaxis()->SetTitle("PU");
  h->GetYaxis()->SetTitle("Sigma_Z [cm]");
  TCanvas * c = new TCanvas("c", "c", 1024, 768);
  //  h->Draw("cont4z"); // Had to drop cont4z since it does not
  //  support TText on top...
  TText * t;
  TMarker * m;
  h->Draw("colz");
  DrawTextAndMarker(32, 4.2, 20, "  (32, 4.2)", &t, &m);
  DrawTextAndMarker(36, 3.8, 20, "  (36, 3.8)", &t, &m);
  DrawTextAndMarker(38, 3.6, 20, "  (38, 3.6)", &t, &m);
  DrawTextAndMarker(17, 5, 20, "  (17, 5) Fill 4569/Run 260627", &t, &m);
  DrawTextAndMarker(12, 4, 20, "  (12, 4) Fill 4479/Run 258714", &t, &m);
  c->Update();
  c->SaveAs("experiment.png");
}

