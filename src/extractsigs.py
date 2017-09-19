#!/usr/bin/env python

####
#
# JOE SANDBOX EXTRACT SCRIPT
#
# Parses all XML reports within a directory and extracts the matching signatures
#
# Change History:

#    04.09.2013:
#        - added "ID" prefix to printout
#       - added unique list of matched signatures as final printout
#           (could be used to extract sig coverage)
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
        print "Usage: extractsigs dir_to_search"

def evalDir(dir):
    touched_sigs = {}
    for r,d,f in os.walk(dir):
        for file in f:
            file = r + os.sep + file
            if not os.path.isdir(file) and file.endswith(".xml"):
                evalFile(file, touched_sigs)
    print "Unique list of used signatures:"
    for key in sorted(touched_sigs.iterkeys()):
        sig = touched_sigs[key]
        print "%s: %s" % (sig.attrib["id"], sig.attrib["desc"])
    print "Total: %d" % len(touched_sigs)

def evalFile(file, touched_sigs):

    high = {}
    sus = {}

    root = et.parse(file)

    md5 = root.find("./fileinfo/md5")

    if md5 != None:
        md5 = md5.text
    else:
        md5 = "unknown"

    sigs = root.findall("./signatureinfo/sig")

    print "Sample %s" % md5

    for sig in sigs:
        if "id" in sig.attrib and "desc" in sig.attrib and "impact" in sig.attrib:
            print "%s: %s -> impact level %s" % (sig.attrib["id"], sig.attrib["desc"], sig.attrib["impact"])
            touched_sigs[sig.attrib["id"].zfill(4)] = sig

if __name__=="__main__":
    main()
