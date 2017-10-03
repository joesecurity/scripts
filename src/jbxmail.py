#!/usr/bin/env python

from __future__ import print_function

import io
import jbxapi
import imaplib
import itertools
import email

##########################
# SETTINGS               #
##########################

# imap settings
SERVER="mail.example.net"
USERNAME="username"
PASSWORD="password"
FOLDER="INBOX"

# API URL.
API_URL  = "https://jbxcloud.joesecurity.org/api"
# for on-premise installations, use the following
# API_URL = "http://" + webserveraddress + "/joesandbox/index.php/api"

# APIKEY, to generate goto user settings - API key
API_KEY = ""

# (for Joe Sandbox Cloud only)
# Set to True if you agree to the Terms and Conditions.
# https://jbxcloud.joesecurity.org/resources/termsandconditions.pdf
ACCEPT_TAC  = False

# default submission parameters
# when specifying None, the server decides
submission_defaults = {
    # system selection, set to None for automatic selection
    # 'systems': ('w7', 'w7x64'),
    'systems': None,
    # comment for an analysis
    'comments': None,
    # maximum analysis time
    'analysis-time': None,
    # password for decrypting office files
    'office-files-password': None,
    # country for routing internet through
    'localized-internet-country': None,
    # tags
    'tags': None,
    # enable internet access during analysis
    'internet-access': None,
    # lookup samples in the report cache
    'report-cache': None,
    # hybrid code analysis
    'hybrid-code-analysis': None,
    # hybrid decompilation
    'hybrid-decompilation': None,
    # adaptive internet simulation
    'adaptive-internet-simulation': None,
    # inspect ssl traffic
    'ssl-inspection': None,
    # instrumentation of vba scripts
    'vba-instrumentation': None,
    # automatically re-submit dropped PE files if they were not executed by the sample
    'autosubmit-dropped': None,
    # send an e-mail upon completion of the analysis
    'email-notification': None,

    ## JOE SANDBOX CLOUD EXCLUSIVE PARAMETERS

    # filter benign samples
    'smart-filter': None,
    # select hyper mode for a faster but less thorough analysis
    'hyper-mode': None,
    # export the report to Joe Sandbox View
    'export-to-jbxview': None,

    ## ON PREMISE EXCLUSIVE PARAMETERS

    # priority of submissions
    'priority': None,
}


def main():
    joe = jbxapi.JoeSandbox(apiurl=API_URL, apikey=API_KEY, accept_tac=ACCEPT_TAC)

    print("Connecting to {0} ...".format(SERVER))
    imap = imaplib.IMAP4_SSL(SERVER)
    print("Logging in as {0} ...".format(USERNAME))
    imap.login(USERNAME, PASSWORD)

    # get message ids
    msg_ids = fetch_message_ids(imap)
    print("Found {0} unread mail(s).".format(len(msg_ids)))

    # extract attachements
    def attachements():
        for msg_id in msg_ids:
            message = read_message(imap, msg_id)
            for name, content in extract_attachements(message):
                yield msg_id, name, content

    count = 0
    for msg_id, name, content in attachements():
        try:
            data = submit_sample(joe, name, content)
        except:
            # if the submission fails we reset the seen flag
            unset_seen_flag(imap, msg_id)
            raise
        else:
            count += 1
        print("Submitted {0} to Joe Sandbox with webid: {1}".format(name, ", ".join(data["webids"])))

    print("======================================================")
    if count:
        print("Submitted {0} samples for analysis.".format(count))
    else:
        print("No new attachement found.")
    print("======================================================")

def extract_attachements(msg):
    """
    Yield name + content
    """
    for part in msg.walk():
        if part.is_multipart():
            continue

        if part.get('Content-Disposition') is None:
            continue

        filename = part.get_filename(failobj="sample")
        sample = part.get_payload(decode=True)

        if len(sample) == 0:
            continue

        yield filename, sample


def submit_sample(joe, name, content):
    fp = io.BytesIO(content)
    fp.name = name

    return joe.submit_sample(fp, params=submission_defaults)

def fetch_message_ids(imap):
    ret, data = imap.select(FOLDER)

    if ret != "OK":
        raise RuntimeError(data)

    ret, data = imap.search(None, 'UNSEEN')
    if ret != "OK":
        raise RuntimeError(data)

    return data[0].split()

def unset_seen_flag(imap, msg_id):
    imap.store(msg_id, '-FLAGS', "\\SEEN")

def read_message(imap, msg_id):
    ret, data = imap.fetch(msg_id, '(RFC822)')
    if ret != "OK":
        raise RuntimeError(data)

    # data[0][1] is bytes in Python 3 and str in Python 2
    if isinstance(data[0][1], str):
        return email.message_from_string(data[0][1])
    else:
        return email.message_from_bytes(data[0][1])

if __name__=="__main__":
    main()
