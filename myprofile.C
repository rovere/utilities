
int plot(char filename[]="dummy.txt",char fileout[]="perf.png")
{ 
#define MAXPOINT 150000
  
  int pid[MAXPOINT],ppid[MAXPOINT];
  float rss[MAXPOINT],vsize[MAXPOINT],pcpu[MAXPOINT],pmem[MAXPOINT];
  float time[MAXPOINT];
  float ex[MAXPOINT],ey[MAXPOINT];
  char line[200];
  printf("Opening file: %s\n",filename);

  ifstream dumpfile;
  dumpfile.open(filename,ifstream::in);
  int curr=0;
  while (1) {
    dumpfile.getline(line,200);
    printf("line = %s\n",line);
    //    std::cout << dumpfile.good() << std::endl;
    if (!dumpfile.good()) 
      {
	printf("Something wrong.....\n");
	break;
      }
    sscanf(line,"%d %d %f %f %f %f",
	   &pid[curr],&ppid[curr],&rss[curr],
	   &vsize[curr],&pcpu[curr],&pmem[curr]);
    time[curr]=curr;
    curr++;
  }
  printf("Read %d lines from file\n",curr);
  char graph_tit[80];
  TGraph *gr_rss = new TGraphErrors(curr,time,rss);
  TGraph *gr_vsize = new TGraphErrors(curr,time,vsize);
  TGraph *gr_pcpu = new TGraphErrors(curr,time,pcpu);
  TGraph *gr_pmem = new TGraphErrors(curr,time,pmem);

  sprintf(graph_tit,"RSS vs time");
  gr_rss->SetTitle(graph_tit);
  gr_rss->SetMarkerColor(2);
  gr_rss->SetMarkerStyle(20);
  gr_rss->SetMarkerSize(0.8);

  sprintf(graph_tit,"VSIZE vs time");
  gr_vsize->SetTitle(graph_tit);
  gr_vsize->SetMarkerColor(2);
  gr_vsize->SetMarkerStyle(20);
  gr_vsize->SetMarkerSize(0.8);

  sprintf(graph_tit,"PCPU vs time");
  gr_pcpu->SetTitle(graph_tit);
  gr_pcpu->SetMarkerColor(2);
  gr_pcpu->SetMarkerStyle(20);
  gr_pcpu->SetMarkerSize(0.8);

  sprintf(graph_tit,"PMEM vs time");
  gr_pmem->SetTitle(graph_tit);
  gr_pmem->SetMarkerColor(2);
  gr_pmem->SetMarkerStyle(20);
  gr_pmem->SetMarkerSize(0.8);

 
  //  gStyle->SetStyle("plain");
  TCanvas* c1 = new TCanvas("c1","c1",1024,768);
  //  c1->SetFrameFillColor(4000);


  c1->Divide(2,2);
  c1->cd(1);
  gr_rss->Draw("ALP");
  c1->cd(2);
  gr_vsize->Draw("ALP");
  c1->cd(3);
  gr_pcpu->Draw("ALP");
  c1->cd(4);
  gr_pmem->Draw("ALP");
  c1->Update();
  c1->Print(fileout);
  
  return;
}
    
 

 
 
