#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import jbxapi
import argparse
import time
import errno
import collections
import random
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

######################################
#             SETTINGS               #
######################################

# Specify the urls and api keys to use for load-balancing.
SERVERS = [
    ("http://127.0.0.1/joesandbox/index.php/api",        "YOUR_API_KEY"),
    ("http://joe1.example.net/joesandbox/index.php/api", "YOUR_API_KEY"),
    ("http://joe2.example.net/joesandbox/index.php/api", "YOUR_API_KEY"),
]

if not hasattr(jbxapi, "JoeSandbox"):
    sys.exit("Jbxapi.py is invalid. Are you using the most recent version?")

Submission = collections.namedtuple('Submission', ['name', 'webid'])


def main(args):
    # command line interface
    parser = argparse.ArgumentParser(description='Submit samples, directories or URLs to the server with the shortest queue. Uses jbxapi.py. Please set your submission options there.')
    parser.add_argument('path_or_url', metavar="PATH_OR_URL", help='Path to file or directory, or URL.')
    
    group = parser.add_argument_group("submission mode")
    submission_mode_parser = group.add_mutually_exclusive_group(required=False)
    submission_mode_parser.add_argument('--url', dest="url_mode", action="store_true",
            help="Analyse the given URL instead of a sample.")
    submission_mode_parser.add_argument('--sample-url', dest="sample_url_mode", action="store_true",
            help="Download the sample from the given url.")
    
    parser.add_argument("--comments", default=None, help='comments (optional')
    parser.add_argument("--wait-for-results", "-wait", action="store_true", help='Set this option to let the script wait for the end of the analysis')
    parser.add_argument("--outdir", "-o", help='Directory for saving the xml reports (optional)')
    args = parser.parse_args()

    if args.outdir is not None:
        if not os.path.isdir(args.outdir):
            sys.exit("Output directory does not exist")

    # prepare servers
    joes = [jbxapi.JoeSandbox(apiurl=url, apikey=key) for url, key in SERVERS]

    job_queues = {joe: [] for joe in joes}
    
    params={"comments": args.comments}
    
    success=False
    
	# Try to submit to best server, if it fails continue until no server is left
    while joes and not success:
        try:
            joe = pick_best_joe(joes)
        except AllServersOfflineError as e:
            print("Failed to fetch any server: ", e , file=sys.stderr)
    
        if args.url_mode or args.sample_url_mode:
            success = submit_url(args, joe, job_queues, params)
        else:
            success = submit_sample(args, joe, job_queues, params)

        if success:
            break
            
        joes.remove(joe)
        
    if not joes and not success:
        print("No more servers to submit to, submission failed", file=sys.stderr)          
        
    def job_count():
        return sum(len(jobs) for jobs in job_queues.values())

    print("Submitted {0} sample(s).".format(job_count()))
    
    if not args.wait_for_results:
        return
    
    print("Waiting for the analyses to finish ...".format(job_count()))

    # download reports
    while job_count() > 0:
        new_reports = 0
        for joe, job_queue in job_queues.items():
            # no jobs in queue
            if not job_queue:
                continue

            submission = job_queue[0]
            info = joe.info(submission.webid)
            if info["status"] == "finished":
                job_queue.pop(0)
                new_reports += 1

                handle_finished_analysis(joe, submission, info, args.outdir)

        # sleep if no new reports were found last time
        if not new_reports:
            for i in range(60 * 5):
                print_progress(job_count())
                time.sleep(.2)

def submit_url(args, joe, job_queues, params):
    '''
    Tries to commit a URL to the server joe
    Returns true if it was successful, False otherwise
    '''
    
    try:
        if args.url_mode:
            data = joe.submit_url(args.path_or_url, params=params)
        else:
            data = joe.submit_sample_url(args.path_or_url, params=params)
        print("Submitted '{0}' with webid(s): {1} to server: {2}".format(args.path_or_url, ",".join(data["webids"]),joe.apiurl))          
        for webid in data["webids"]:
            job_queues[joe].append(Submission(args.path_or_url, webid))
        return True
    except Exception as e:
        print("Submitting '{0}' failed: {1}".format(args.path_or_url, e))
        return False
                
def submit_sample(args, joe, job_queues, params):               
    '''
    Tries to commit a sample or directory to the server joe
    Returns true if at least one sample submission was successful, False otherwise
    '''

    # if given a directory, collect all files
    if os.path.isdir(args.path_or_url):
        paths = [os.path.join(args.path_or_url, name) for name in os.listdir(args.path_or_url)]
    else:
        paths = [args.path_or_url]
        
    for path in paths:
        name = os.path.basename(path)
        try:
            with open(path, "rb") as f:
                data = joe.submit_sample(f, params=params)

            print("Submitted '{0}' with webid(s): {1} to server: {2}".format(args.path_or_url, ",".join(data["webids"]),joe.apiurl))   
            for webid in data["webids"]:
                job_queues[joe].append(Submission(name, webid))         
        except Exception as e:
            print("Submitting '{0}' failed: {1}".format(name, e), file=sys.stderr)
        
    # If at least one submission worked, return True
    if job_queues[joe]:
        return True
    else:
        return False
            
def handle_finished_analysis(joe, submission, info, outdir):
    # download best run
    filename, data = joe.download(submission.webid, "xml")

    # save to disk
    if outdir is not None:
        with open(os.path.join(outdir, filename), "wb") as f:
            f.write(data)

    # parse xml so we can report the detection or errors
    root = ET.fromstring(data)
    detection = root.find("signaturedetections/strategy[@name='empiric']/detection").text

    if detection == "CLEAN":
        detection = "clean"
    elif detection == "SUS":
        detection = "suspicious"
    elif detection == "MAL":
        detection = "malicious"
    elif detection == "UNKNOWN":
        detection = "unknown"

    errors = [el.text for el in root.findall("errorinfo/error")]

    print()
    print("Analysis finished:")
    print("  filename: ", submission.name)
    print("  md5:      ", info["md5"])
    print("  sha1:     ", info["sha1"])
    print("  sha256:   ", info["sha256"])
    print("  detection:", detection)
    for error in errors:
        print("  error:", error)
    print()


def print_progress(value):
    progressbar = list("--------------------")
    index = int(round((time.time() * 5) % (len(progressbar) * 2 - 2)))
    if index >= len(progressbar):
        index = len(progressbar) - index - 2

    progressbar[index] = "+"
    progressbar = "[" + "".join(progressbar) + "]"

    # empty space so we can overwrite the line
    print(progressbar, "({})      ".format(value), end="\r")
    sys.stdout.flush()


class AllServersOfflineError(Exception): pass


def pick_best_joe(joes):
    """
    Picks the best server to submit to
    The best server is the one with the lowest queuesize
    If several servers have the same queuesize, a random one is returned
    """
    current_min = None
    min_joes = []
    for joe in joes:
        try:
            queuesize = joe.server_info()["queuesize"]
            if not current_min:
                current_min = joe.server_info()["queuesize"]
                min_joes.append(joe)
            else:           
                if queuesize < current_min:
                    current_min = queuesize
                    del min_joes[:]
                    min_joes.append(joe)
                elif queuesize == current_min:
                    min_joes.append(joe)
        except jbxapi.ServerOfflineError:
            pass

    if not min_joes:
        raise AllServersOfflineError("All servers are offline.")

    return random.choice(min_joes)


if __name__ == "__main__":
    main(sys.argv)