Scripts
=======

This repository contains some useful scripts for interaction with Joe Sandbox.

The scripts make use of [`jbxapi.py`][jbxapi], a lightweight module to interact with the API. Install it by copying it to your current working directory or use pip for installation:

    pip install git+https://github.com/joesecurity/joesandboxcloudapi@v1.0.0#egg=jbxapi

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
