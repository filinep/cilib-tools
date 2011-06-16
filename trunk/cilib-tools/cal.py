#!/usr/bin/python
import sys
import copy
import os.path
import csv
import scipy
import matplotlib.pyplot as Plot

class Group():
    def __init__(self, folder, *args):
        if folder is not None:
            self.simulations = []
            self.groups = []
            self.parent = None
            self.properties = {"dimension":[], "algorithm":[], "problem":[]}
            self.type = "all"
            self.value = "all"

            dirList = os.listdir(folder)
            for fname in [os.path.join(folder, f) for f in dirList if os.path.isfile(os.path.join(folder, f))]:
                split = fname.replace(".txt", "").split("/")[-1].split("+")

                if split[0] not in self.properties["dimension"]:
                    self.properties["dimension"].append(float(split[0]))
                if split[1] not in self.properties["problem"]:
                    self.properties["problem"].append(split[1])
                if split[2] not in self.properties["algorithm"]:
                    self.properties["algorithm"].append(split[2])

                self.simulations.append(Simulation(fname))

            for k in self.properties.keys():
                self.properties[k].sort()
        else:
            #args = (simulations, properties, parent, t, v):
            self.properties = args[1] #properties
            self.simulations = args[0] #simulations
            self.parent = args[2] #parent
            self.groups = []
            self.type = args[3] #t
            self.value = args[4] #v

    def groupby(self, t):
        for v in self.properties[t]:
            props = copy.deepcopy(self.properties)
            del(props[t])
            props[t] = [v]

            sims = [sim for sim in self.simulations if sim.properties[t] == v]
            self.groups.append(Group(None, sims, props, self, t, v))
        return self.groups

    def __iter__(self):
        return self.simulations.__iter__()

    def __len__(self):
        return len(self.simulations)

    def __contains__(self, v):
        return v in self.simulations

    def __getitem__(self, v):
        return self.simulations[v] 

class Simulation():
    def __init__(self, fname):
        self.properties = {"dimension":0, "algorithm":"", "problem":""}

        self.file = fname
        self.measurements = {}
        self.samples = 0
        self.read_header()
        
        split = fname.replace(".txt", "").split("/")[-1].split("+")

        self.properties["dimension"] = float(split[0])
        self.properties["problem"] = split[1]
        self.properties["algorithm"] = split[2]

    def read_header(self):
        data = csv.reader(open(self.file, "r"), delimiter=' ')
        for row in data:
            if row[0] == "#":
                if row[3] in self.measurements.keys():
                    self.measurements[row[3]]["range"].append(int(row[1]))
                else:
                    self.measurements[row[3]] = {"range":[int(row[1])]}

                if len(row) > 4:
                    self.samples = max(self.samples, int(row[4].replace(")", "").replace("(", "")) + 1)
            else:
                #assume the first non-hash line means no more header
                return

    def get_measurement(self, m):
        data = csv.reader(open(self.file, "r"), delimiter=' ')
        ret = []
        for row in data:
            if not row[0] == "#":
                ret.append([i for i in 
                            row[min(self.measurements[m]["range"]):max(self.measurements[m]["range"]) + 1]
                          ])
        return ret

def foreach(li, f, par=None):
    ret = []
    for i in li:
        ret.append(f(i, par))
    """if type(ret[0]) == list:
        return [item for sublist in ret for item in sublist]"""
    return ret

def measure(sim, m):
    return sim.get_measurement(m)

def rows(sim, m):
    return sim.get_measurement(m)

def composite(li, data=None):
    ret = []
    for i in li:
        ret.append([float(x.replace("[", "").replace("]", "")) for x in i.split(",")])
    return ret

def columns(li, data=None):
    return [[x[i] for x in li] for i in range(len(li[0]))]

def mean(li, data):
    if type(li[0]) == list:
        return [scipy.mean([x[i] for x in li]) for i in range(len(li[0])) ]
    return scipy.mean([float(i) for i in li])

def stddev(li, data):
    if type(li[0]) == list:
        return [scipy.std([x[i] for x in li]) for i in range(len(li[0])) ]
    return scipy.std([float(i) for i in li])

def groupby(gr, t):
    return gr.groupby(t)

def minlist(li):
    return min(li)

def maxlist(li):
    return max(li)

def rank(gr, vals, f):
    ret = []
    sims = copy.deepcopy(gr.simulations)
    while not sims == []:
        index = vals.index(f(vals))

def plotnew(xaxis, yaxis):
    Plot.clf()
    Plot.ylabel(yaxis)
    Plot.xlabel(xaxis)

def plotadd(x, y, name, symbol, limit=None):
    if limit is not None:
        x = [i for i in x if i <= limit]
        y = y[:len(x)]

    Plot.plot(x, y, symbol, label=name)
    Plot.plot(x, y, "-", label=name)

def plotsave(name):
    Plot.savefig(name, format="png")

def plot_measurement(group, groups, xMeasure, yMeasure, xName, yName, limit):
    if groups == []:
        plotnew(xName, yName)

        for s in group:
            plotadd(foreach(measure(s, xMeasure), mean),
                    foreach(measure(s, yMeasure), mean),
                    s.properties["algorithm"], "o", limit)

        parent = group
        savename = yMeasure
        while parent is not None and parent.parent is not None:
            savename += parent.value
            parent = parent.parent

        plotsave("/home/filipe/Desktop/b/" + savename + ".png")
    else:
        toGroup = groups[-1]
        del(groups[-1])
        for g in groupby(group, toGroup):
            plot_measurement(g, groups, xMeasure, yMeasure, xName, yName, limit)

def plot_composite(group, groups, xMeasure, yMeasure, xName, yName, limit):
    if groups == []:
        for s in group:
            plotnew(xName, yName)
            for c in columns(
                        foreach(
                                foreach(
                                        measure(s, yMeasure),
                                    composite),
                            mean)
                         ):
                plotadd(foreach(measure(s, xMeasure), mean),
                        c, "a", "o", 30000)

            parent = group
            savename = yMeasure
            while parent is not None and parent.parent is not None:
                savename += parent.value
                parent = parent.parent

            plotsave("/home/filipe/Desktop/b/" + savename + ".png")
    else:
        toGroup = groups[-1]
        del(groups[-1])
        for g in groupby(group, toGroup):
            plot_composite(g, groups, xMeasure, yMeasure, xName, yName, limit)

#plot_measurement(Group("/home/filipe/Desktop/a"), ["problem", "dimension"], "FitnessEvaluations", "Fitness", "FitnessEvaluations","Fitness", 30000)
#plot_composite(Group("/home/filipe/Desktop/a"), ["problem", "dimension", "algorithm"], "FitnessEvaluations", "AdaptiveHPSOBehaviorProfileMeasurement", "FitnessEvaluations", "BehaviorCount", 30000)

g = Group("/home/filipe/Desktop/a")
for g1 in groupby(g, "problem"):
    plotnew("Dimensions", "Fitness")

    xPlot = [float(x) for x in g1.properties["dimension"]]
    yPlots = {}

    for g2 in groupby(g1, "dimension"):
        for s in g2:
            if s.properties["algorithm"] not in yPlots.keys():
                yPlots[s.properties["algorithm"]] = [foreach(measure(s, "Fitness"), mean)[-1]]
            else:
                yPlots[s.properties["algorithm"]].append(foreach(measure(s, "Fitness"), mean)[-1])

    for k in yPlots.keys():
        print yPlots[k]
        plotadd(xPlot, yPlots[k], k, "o")

    parent = g1
    savename = "Dimension"
    while parent is not None and parent.parent is not None:
        savename += parent.value
        parent = parent.parent

    plotsave("/home/filipe/Desktop/b/" + savename + ".png")


