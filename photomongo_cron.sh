#!/bin/bash
#
# This is meant to be a wrapper for photomongo.py to run as a cron job.
# Because I used a virtualenv to run photomongo, I needed a simple way
# to wrap up the commands to the shell.

# set directory
MONGO_DIR=$HOME/proj/face_detect

# start the virtual environment
source $MONGO_DIR/bin/activate

# change to the photomongo directory
cd $MONGO_DIR/photomongo

# run the command
python3 photomongo.py mongo.conf --since=1 

