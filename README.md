Scripts
=======

This repository contains some useful scripts for interaction with Joe Sandbox.

 * jbxbalancer.py : Submit samples to multiple Joe Sandbox instances
                    choosing the one with the shortest queue.
 * jbxmail.py :     Download files from an e-mail account and analyze attachements of
                    unread mails.
 * extractsigs.py : Extract the behavior signatures from downloaded XML reports.
 * extractscore.py : Extract the score from downloaded XML reports.

Some of the scripts depend on [`jbxapi.py`][jbxapi], a lightweight module for interaction with Joe Sandbox. Install it by copying it to your current working directory or use pip for installation:

    pip install git+https://github.com/joesecurity/joesandboxcloudapi@v2#egg=jbxapi

 [jbxapi]: https://github.com/joesecurity/joesandboxcloudapi

`jbxbalancer.py`
----------------

Use this script to submit samples to one of multiple Joe Sandbox installations.
Before submitting a sample the script queries the queue length and submits the sample
to the server with the shortest queue.

To use the scripts, specify the servers by changing the `SERVERS` variable. Then use it as
follows:

    > ./jbxbalancer.py --help
    usage: jbxbalancer.py [-h] [--comment COMMENT] PATH

    Submit samples to the server with the shortest queue.

    positional arguments:
      PATH               Path to file or directory.

    optional arguments:
      -h, --help         show this help message and exit
      --comment COMMENT

`jbxmail.py`
------------

`extractsigs.py`
----------------

   Usage: ./extractsigs dir_to_search

`extractscore.py`
-----------------

   Usage: ./extractscore dir_to_search


