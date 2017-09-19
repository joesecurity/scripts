####
#
# JOE SANDBOX EXTRACT SCORE SCRIPT
#
# Parses all XML reports within a directory and extracts the detection and score
#

import xml.etree.cElementTree as et
import os, stat, sys, time
import pickle
import itertools
import operator

def main():

    if len(sys.argv) == 2:
        evalDir(sys.argv[1])
    else:
        print "Usage: extractscore dir_to_search"

def evalDir(dir):
    touched_sigs = {}
    for r,d,f in os.walk(dir):
        for file in f:
            filepath = r + os.sep + file
            if file == "report.xml":
                try:
                    evalFile(filepath, touched_sigs)
                except:
                    print "Unable to parse " + file

def evalFile(file, touched_sigs):

    root = et.parse(file)

    md5 = root.find("./fileinfo/md5")

    if md5 != None:
        md5 = md5.text
    else:
        md5 = "unknown"

    det = root.find("./signaturedetections/strategy[@name='empiric']/detection")
    score = root.find("./signaturedetections/strategy[@name='empiric']/score")
    error = root.find("./errorinfo/error")

    if error != None:
        error = error.text
    else:
        error = ""

    print md5 + "," + det.text + "," + score.text + ",\"" + error + "\""

if __name__=="__main__":
    main()
