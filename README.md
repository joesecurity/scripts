Joe Sandbox Scripts
===================


This repository contains some useful scripts for interaction with Joe Sandbox.

<dl>
<dt>jbxbalancer.py</dt>
<dd>
    Submit samples to multiple instances of Joe
    Sandbox. The script load-balances the submissions
    by choosing the instance with the shortest queue.
</td>
<dt>jbxmail.py</dt>
<dd>
    Download files from an e-mail account and analyze
    attachements of unread mails.
</dd>
<dt>extractsigs.py</dt>
<dd>
    Extract the behavior signatures from downloaded
    XML reports.
</dd>
<dt>extractscore.py</dt>
<dd>
    Extract the score from downloaded XML reports.
</dd>
</table>

Some of the scripts depend on [`jbxapi.py`][jbxapi], a lightweight module for interaction with Joe Sandbox. Install it by copying it to your current working directory or use pip for installation:

    pip install git+https://github.com/joesecurity/joesandboxcloudapi@v2#egg=jbxapi

License
-------

All scripts in this repository are licensed under the [MIT license](LICENSE.txt).

`jbxbalancer.py`
----------------

**Requirements:** Python 2.7 or 3.3, [`jbxapi.py`][jbxapi]

Use this script to submit samples to one of multiple Joe Sandbox installations.
Before submitting a sample the script queries the queue length and submits the sample
to the server with the shortest queue.

To use the scripts, specify the servers by changing the `SERVERS` variable. Please also set your submission defaults in jbxapi.py. 
Then use it as follows:

    > ./jbxbalancer.py --help
    usage: jbxbalancer-oem.py [-h] [--url | --sample-url] [--comments COMMENTS]
                              [--wait-for-results] [--outdir OUTDIR]
                              PATH_OR_URL
                              
    Submit samples, directories or URLs to the server with the shortest queue.
    Uses jbxapi.py. Please set your submission options there.

    positional arguments:
      PATH_OR_URL           Path to file or directory.

    optional arguments:
      -h, --help            show this help message and exit
      --comments COMMENTS   comments (optional
      --wait-for-results, -wait
                            Set this option to let the script wait for the end of
                            the analysis
      --outdir OUTDIR, -o OUTDIR
                            Directory for saving the xml reports (optional)

    submission mode:
      --url                 Analyse the given URL instead of a sample.
      --sample-url          Download the sample from the given url.

`jbxmail.py`
------------

**Requirements:** Python 2.7 or 3.3, [`jbxapi.py`][jbxapi]

Use this script to analyse e-mail attachments of an IMAP mailbox. Simply adapt the following variables:
`SERVER`, `USERNAME`, `PASSWORD`, `API_URL`, `API_KEY`, `ACCEPT_TAC` and modify the submission parameters to your liking.

Then call it as follows:

    > ./jbxmail.py
    Connecting to imap.example.net ...
    Logging in as joe ...
    Found 1 unread mail(s).
    Submitted Invoice.docx.exe to Joe Sandbox with webid: 45212
    Submitted Sample.exe to Joe Sandbox with webid: 45213
    ======================================================
    Submitted 2 samples for analysis.

`extractsigs.py`
----------------

**Requirements:** Python 2.6

Usage:

    ./extractsigs dir_to_search

`extractscore.py`
-----------------

**Requirements:** Python 2.6

Usage:

    ./extractscore dir_to_search

 [jbxapi]: https://github.com/joesecurity/joesandboxcloudapi
