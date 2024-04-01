import sys
import os
import ROOT as r

# Define the colors for the output
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
def DEBUG(text):
    return bcolors.OKGREEN+text+bcolors.ENDC
def TITLE(text):
    return bcolors.OKBLUE+text+bcolors.ENDC
def HEADER(text):
    return bcolors.HEADER+bcolors.BOLD+bcolors.OKBLUE+bcolors.UNDERLINE+text+bcolors.ENDC


# Load the databases
from infofile import infos
from dataSets import dataSets, totRealLum, realList, dataCombos, dirs

# For parallel processing and timing
import multiprocessing
from itertools import product
import time

# For parsing the script arguments
import argparse

# Load the C++ library
sys.path.append('../build/python/.')
from AnalysisFW import CLoop,CLoopConfig

# This is a hack to allow the C++ class to be pickled, see:
# https://www.boost.org/doc/libs/1_84_0/libs/python/doc/html/reference/topics/pickle_support.html
def CLoopConfig_getinitargs(self):
  return (self.m_saveHistograms,self.m_saveEvents,self.m_reweightMjj,self.m_bdtWeightsPath)
# now inject __getinitargs__ (Python is a dynamic language!)
CLoopConfig.__getinitargs__ = CLoopConfig_getinitargs

def getLuminosity(sampleName):
    if "2018" in sampleName:
        return 58.4501
    elif "2017" in sampleName:
        return 43.5873
    else :
        return 36.2369

def getSampleID(sampleName):
    z_sample=0
    if ("Zee" in sampleName) or ("Zmumu" in sampleName) or ("Ztautau" in sampleName):
        z_sample=1
        if "sherpa" in sampleName or "Sherpa" in sampleName:
            z_sample=2
            if "NLO" in sampleName:
                z_sample=4
        if "VBF" in sampleName:
            z_sample=0
        if "MG" in sampleName:
            z_sample=3
            if "NLO" in sampleName:
                z_sample=5
    return z_sample

def getNormalise(sampleName,lumFactor):
    if sampleName in realList:
        return 1.0
    else:
        weight = (lumFactor * 1000 * infos[sampleName]["xsec"] * infos[sampleName]["fil_eff"] * infos[sampleName]["kfac"])/infos[sampleName]["sumw"]
        return weight

def getAbsoluteFilePath(sampleName):
    correctPath = ""
    # Get the filename
    try:
        filename = dataSets[sampleName]
    except KeyError:
        print("Sample ", sampleName, " not defined. Exiting.")
        sys.exit(1)
    # search through several directories to find where the input file is located
    for path in dirs:
        if filename in os.listdir(path):
            correctPath = path
            break

    if correctPath == "":
        print("File for sample ", sampleName, " not found. Exiting.")
        sys.exit(1)

    return correctPath + filename

def getSamplesToRun(option,allData,allMC):
    if option=="All":
        for key,value in dataCombos.items():
            if "data" in key:
                allData+=value
            else:
                if "truth" not in key and "sys" not in key and "old" not in key and "VV_EW_Semi" not in key:
                    allMC+=value
        return
    elif option=="Data":
        for key,value in dataCombos.items():
            if "data" in key:
                allData+=value
        return
    elif option=="MC":
        for key,value in dataCombos.items():
            if "data" not in key:
                if "truth" not in key and "sys" not in key and "old" not in key and "VV_EW_Semi" not in key:
                    allMC+=value
        return
    
def createOutputDirectory(outputPath,treeName,verbosity):
    if not os.path.exists(outputPath):
        if verbosity=="DEBUG":
            print(DEBUG("Creating output directory at: "), os.path.abspath(outputPath))
        os.makedirs(outputPath)
        if verbosity=="DEBUG":
            print(DEBUG("Creating output for tree at: "), os.path.abspath(outputPath)+"/"+treeName)
        os.makedirs(outputPath+"/"+treeName)

def createConfigObject(jobTypeArgument,verbosity):
    makeHistograms = 'h' in jobTypeArgument
    if verbosity=="DEBUG" and makeHistograms:
        print(DEBUG("Making histograms!"))
    makeNTuples = 'n' in jobTypeArgument
    if verbosity=="DEBUG" and makeNTuples:
        print(DEBUG("Making ntuples!"))
    makeReweighting = 'r' in jobTypeArgument
    if verbosity=="DEBUG" and makeReweighting:
        print(DEBUG("Making reweighting!"))
    mvaWeightsPath = "/Users/user/Documents/HEP/MVA-Analysis/dataset/weights/10Folds_BDT-0.3.weights.xml"
    if verbosity=="DEBUG":
        print(DEBUG("MVA weights path: "), mvaWeightsPath)
    return CLoopConfig(makeHistograms,makeNTuples,makeReweighting,mvaWeightsPath)


def runAnalysis(treeName,sampleName,verbosity,outputPath,analysisConfig):
    # Get the absolute path of the file
    filePath = getAbsoluteFilePath(sampleName)
    if verbosity=="DEBUG":
        print(TITLE("Sample name: "), sampleName)
        print(DEBUG("File path: "), filePath)

    # Open root file and get the tree
    file = r.TFile.Open(filePath, "READ")
    tree = r.TTree()
    tree = file.Get(treeName)

    # Get the sample ID
    sampleID = getSampleID(sampleName)
    if verbosity=="DEBUG":
        print(DEBUG("Sample ID: "), sampleID)
    # Get the luminosity
    lumFactor = getLuminosity(sampleName)
    if verbosity=="DEBUG":
        print(DEBUG("Luminosity: "), lumFactor)
    # Get the normalisation weight
    weight = getNormalise(sampleName,lumFactor)
    if verbosity=="DEBUG":
        print(DEBUG("Normalisation weight: "), weight)

    analysis = CLoop(r.addressof(tree), sampleName)
    analysis.Loop(weight, sampleID, sampleName,analysisConfig)
    del analysis
    file.Close()
    success = os.system("mv "+sampleName+".root "+outputPath+"/"+treeName+"/"+sampleName+treeName+".root")
    if success != 0:
        print("Error moving file to Results directory.")
        sys.exit(1)


if __name__ == "__main__":
    # Parse the script arguments
    parser = argparse.ArgumentParser()
    executionMode = parser.add_mutually_exclusive_group()
    executionMode.add_argument("--samples", help="Type of samples to run over.",type=str,choices=["MC","Data","All"],default="All")
    executionMode.add_argument("--singleSample", help="Run over a single sample.",type=str,default="")
    parser.add_argument("--verbose", help="Verbosity level.",type=str,default="INFO",choices=["INFO","DEBUG"])
    parser.add_argument("--treeName", help="Name of the tree to run over.",type=str,default="NOMINAL")
    parser.add_argument("--jobType", help="Type of job to run.",type=str,default="h",choices=["h","n","hn","hr","hnr"])
    parser.add_argument("--outputDir", help="Path of to the directory used to store the processed samples.",type=str,default="../Results")
    parser.add_argument("--j", help="Number of cores to use.",type=int,default=1)
    args = parser.parse_args()

    # Start timer and greet the user
    initTime = time.time()
    print(HEADER("Welcome to the AnalysisFW"))

    # Define debug mode
    verbosity = args.verbose

    # Create the output directory
    createOutputDirectory(args.outputDir,args.treeName,verbosity)

    # Create the config object to pass to CLoop
    config = createConfigObject(args.jobType,verbosity)

    # If a single sample is chosen, run just over that
    if args.singleSample != "":
        runAnalysis(args.treeName,args.singleSample,verbosity,args.outputDir,config)
    else :
        # Select the correct datasets
        allData = []
        allMC = []
        getSamplesToRun(args.samples,allData,allMC)
        dataTuple = product([args.treeName],allData,[verbosity],[args.outputDir], [config])
        mcTuple = product([args.treeName],allMC,[verbosity],[args.outputDir], [config])

        # Define number of cores
        nCPU = args.j if verbosity=="INFO" else 1

        print(TITLE("Running over "+str(len(allData))+" DATA samples\n"))
        with multiprocessing.Pool(processes=nCPU) as pool:
            pool.starmap(runAnalysis, dataTuple)

        print(TITLE("Running over "+str(len(allMC))+" MC samples\n"))
        with multiprocessing.Pool(processes=nCPU) as pool:
            pool.starmap(runAnalysis, mcTuple)

    # Say goodbye and print the time taken
    print(HEADER("Analysis done"))
    print(DEBUG("Time taken: "+str(time.time()-initTime)))
