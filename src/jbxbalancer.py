#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import jbxapi
import argparse
import time
import errno
import collections
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
    parser.add_argument("--type", default="file", help='one of "file", "url", "sample-url" (optional, defaults to "file")') 
    parser.add_argument("--comment", default=None, help='comment (optional')
    parser.add_argument("--waituntilfinished", "-wait", help='Set this option to True to let the script wait for the end of the analysis')
    parser.add_argument("--outdir", "-o", help='Directory for saving the xml reports (optional)')
    args = parser.parse_args()

    if args.outdir is not None:
        if not os.path.isdir(args.outdir):
            sys.exit("Output directory does not exist")

    # prepare servers
    joes = [jbxapi.JoeSandbox(apiurl=url, apikey=key) for url, key in SERVERS]

    # submit all samples
    exceptions = []
    job_queues = {joe: [] for joe in joes}
    
    params={"comments": args.comment}
    
    if args.type == 'url' or args.type == 'sample-url':
        try:
            joe = next_joe(joes)
            if args.type == 'url':
                data = joe.submit_url(args.path_or_url, params=params)
            else:
                data = joe.submit_sample_url(args.path_or_url, params=params)
            print("Submitted '{0}' with webid(s): {1} to server: {2}".format(args.path_or_url, ",".join(data["webids"]),joe.apiurl))          
            for webid in data["webids"]:
                job_queues[joe].append(Submission(args.path_or_url, webid))
        except Exception as e:
            print("Submitting '{0}' failed: {1}".format(args.path_or_url, e), file=sys.stderr)          
    else:
        # if given a directory, collect all files
        if os.path.isdir(args.path_or_url):
            paths = [os.path.join(args.path_or_url, name) for name in os.listdir(args.path_or_url)]
        else:
            paths = [args.path_or_url]
    
        for path in paths:
            name = os.path.basename(path)
            try:
                joe = next_joe(joes)
                with open(path, "rb") as f:
                    data = joe.submit_sample(f, params=params)

                print("Submitted '{0}' with webid(s): {1} to server: {2}".format(args.path_or_url, ",".join(data["webids"]),joe.apiurl))   
                for webid in data["webids"]:
                    job_queues[joe].append(Submission(name, webid))
            except Exception as e:
                exceptions.append((name, e))

    # print intermediate status
    for name, e in exceptions:
        print("Submitting '{0}' failed: {1}".format(name, e), file=sys.stderr)

    def job_count():
        return sum(len(jobs) for jobs in job_queues.values())

    print("Submitted {0} sample(s).".format(job_count()))
    
    if not args.waituntilfinished:
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


def next_joe(joes):
    """
    Figure out to which instance we should submit the next sample.
    """
    queue_sizes = []
    for joe in joes:
        try:
            queue_sizes.append((joe.server_info()["queuesize"], joe))
        except jbxapi.ServerOfflineError:
            pass

    try:
        _, joe = min(queue_sizes, key=lambda x: x[0])
    except ValueError:
        raise AllServersOfflineError("All servers are offline.")

    return joe


if __name__ == "__main__":
    main(sys.argv)
