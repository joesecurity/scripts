#!/usr/bin/env python

from __future__ import print_function
import os
import sys
import jbxapi
import argparse

######################################
#             SETTINGS               #
######################################

# Specify the urls and api keys to use for load-balancing.
SERVERS = [
    ("http://127.0.0.1/joesandbox/index.php/api",        "YOUR_API_KEY"),
    ("http://joe1.example.net/joesandbox/index.php/api", "YOUR_API_KEY"),
    ("http://joe2.example.net/joesandbox/index.php/api", "YOUR_API_KEY"),
]

def main(args):
    # command line interface
    parser = argparse.ArgumentParser(description='Submit samples to the server with the shortest queue.')
    parser.add_argument('file_or_dir', metavar="PATH", help='Path to file or directory.')
    parser.add_argument("--comment", default=None)
    args = parser.parse_args()

    # if given a directory, collect all files
    if os.path.isdir(args.file_or_dir):
        paths = [os.path.join(args.file_or_dir, name) for name in os.listdir(args.file_or_dir)]
    else:
        paths = [args.file_or_dir]

    # prepare servers
    joes = [jbxapi.JoeSandbox(apiurl=url, apikey=key) for url, key in SERVERS]

    # submit all samples
    exceptions = []
    for path in paths:
        name = os.path.basename(path)
        try:
            joe = next_joe(joes)
            with open(path, "rb") as f:
                data = joe.submit_sample(f, params={"comments": args.comment})
            print("Submitted '{0}' with webid(s): {1}".format(name, ",".join(data["webids"])))
        except Exception as e:
            exceptions.append((name, e))

    for name, e in exceptions:
        print("Submitting '{0}' failed: {1}".format(name, e), file=sys.stderr)

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

class API1to2(object):
    """
    Wraps the old joe_api object to expose an interface like the new jbxapi.
    """
    class JoeException(Exception): pass
    class ServerOfflineError(JoeException): pass

    @classmethod
    def install(cls, module):
        module.JoeSandbox = cls
        module.ServerOfflineError = cls.ServerOfflineError

    def __init__(self, apikey, apiurl):
        apiurl = apiurl.rstrip("/") + "/"
        self._wrapped = jbxapi.joe_api(apikey=apikey, apiurl=apiurl)

    def server_info(self):
        try:
            return {"queuesize": self._wrapped.queue_size()}
        except ValueError as e:
            if e.message.startswith("invalid literal for int() with base 10"):
                message = e.message[41:-1]
            else:
                message = e.message
            self._raise_exception(message)

    def submit_sample(self, file, params={}):
        response = self._wrapped.analyze(file, "", comments=params["comments"])
        try:
            return {"webids": [str(webid) for webid in response["webids"]]}
        except TypeError:
            self._raise_exception(response)

    def _raise_exception(self, message):
        if "maintenance" in message:
            raise self.ServerOfflineError(message)
        else:
            raise self.JoeException(message)

# add compatiblity layer for the old jbxapi using APIv1
if not hasattr(jbxapi, "JoeSandbox"):
    API1to2.install(jbxapi)

if __name__ == "__main__":
    main(sys.argv)
