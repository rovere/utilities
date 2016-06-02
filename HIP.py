from ROOT import TF1, TCanvas, TFile, TGraphErrors
from math import exp

def ineff_hip(x, a, b):
    """
    Inefficiency curve with HIP.
    a is the rate at which the HIP centers are created.
    b is the rate at which the effect of the HIP center is recovered in the SiStrip
    a/b is the asymptotic value towards which the inefficiency converges after enought time has elapsed(inf)
    By design the inefficiency always starts at 0 at x=0
    """
    return (a-a*exp(-b*x))/b

def eff_hip(x, a, b, c):
    """
    Efficiency curve with HIP.
    a is the rate at which the HIP centers are created.
    b is the rate at which the effect of the HIP center is recovered in the SiStrip
    c is the starting value of the efficiency
    c - a/b is the asymptotic value towards which the efficiency converges, after enought time has elapsed(inf)
    """
    return c - ineff_hip(x, a, b)

def ineff_noHIP(x, b, k):
    """
    Ordinary inefficiency function in absence of HIP.
    k is the starting value of the curve at x=0
    The curves naturally goes to 0 for big enough x(inf)
    """
    return k*exp(-b*x)

def eff_noHIP(x, b, c, k):
    """
    Ordinary efficiency function in absence of HIP
    The starting value of the function at x=0 is c-k
    The function naturally converges to the value c, for big enough x(inf)
    """
    return c - ineff_noHIP(x, b, k)

class Eff_hip_corr:
    def __init__(self, t):
        self.intervals = t
        print self.intervals
    # par[0] ==> a
    # par[1] ==> b
    # par[2] ==> c
    def __call__(self, x, par):
        for (value, kind) in self.intervals:
            if x[0] > value[0] and x[0] <= value[1]:
                if kind == 'eff_HIP1':
                    return eff_hip(x[0] - value[0], par[0], par[1], par[2])
                elif kind == 'eff_HIP':
                    return eff_hip(x[0] - value[0], par[0], par[1], self.__call__([value[0],0,0,0], par))
                elif kind == 'eff_noHIP':
                    return eff_noHIP(x[0] - value[0], par[1], par[2], par[2] - self.__call__([value[0],0,0,0], par))
                else:
                    return 0
        return 0

if __name__ == '__main__':
    f = []
    input_files = []
    gr = []
    c = TCanvas("c", "c", 1024, 1024)
    f.append(TF1('pyf2',Eff_hip_corr([([143,769], 'eff_HIP1'),
                                      ([769,1037], 'eff_noHIP'),
                                      ([1037,1663], 'eff_HIP'),
                                      ([1663,1931], 'eff_noHIP'),
                                      ([1931,2557], 'eff_HIP'),
                                      ([2557,2825], 'eff_noHIP'),
                                      ([2825,3229], 'eff_HIP')
                                  ]),143.,2000.,3))
    f.append(TF1('pyf2',Eff_hip_corr([([183,351], 'eff_HIP1'),
                                      ([351,1077], 'eff_noHIP'),
                                      ([1077,1245], 'eff_HIP'),
                                      ([1245,1971], 'eff_noHIP'),
                                      ([1971,2139], 'eff_HIP'),
                                      ([2139,2671], 'eff_noHIP'),
                                      ([2671,2750], 'eff_HIP'),
                                      ([2750,2865], 'eff_noHIP'),
                                      ([2865,2944], 'eff_HIP'),
                                      ([2944, 2954], 'eff_noHIP'),
                                      ([2954,3033], 'eff_HIP')
                                  ]),183.,3033.,3))
    f.append(f[-1])
    for i in range(len(f)):
        f[i].SetParameters(1./600., 1./500., 0.9)

    input_files.append(TFile('TIBLayer2_plots_SingleMuon_Run258425.root'))
    input_files.append(TFile('TIBLayer1_plots_SingleMuon_Run259721.root'))
    input_files.append(TFile('TOBLayer1_plots_SingleMuon_Run259721.root'))
    for i in range(len(input_files)):
        gr.append(input_files[i].Get('Graph'))
        gr[i].Fit(f[i])
        # print results
        par = f[i].GetParameters()
        print 'fit results: a =',par[0],',b =',par[1], 'c =', par[2]
        # plot the function
        gr[i].Draw('AP')
    #    f.Draw()
        c.SaveAs('eureka_%d.pdf' %i)
        try:
            mode = raw_input('Input:')
        except ValueError:
            print "Not a number"

