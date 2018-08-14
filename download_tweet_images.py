#!/usr/bin/env pytohon
"""
download_tweet_images.py

Usage:
  download_tweet_images.py [options] CONFIGFILE DESTINATION

Options:
  -h --help          Show this screen
  --since=<days>     Maximum number of days to get in the past
  --max=<number>     Maximum number to get
  --no-progress-bar  Display the progress bar

"""

import sys
import logging
logging.basicConfig(level=logging.DEBUG,
                    handlers = [logging.FileHandler('dowload_tweet_images.log')] ) 

log = logging.getLogger(__name__)

import os
from docopt import docopt
import configparser
import json
import wget

from twitter import Twitter
import progress_bar

# control logging level of modules
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("oauthlib").setLevel(logging.WARNING)
logging.getLogger("tweepy").setLevel(logging.WARNING)

if __name__=='__main__':
    
    args = docopt(__doc__)

    try:
        maxCount = int(args['--max'])
    except ( KeyError, TypeError ):
        maxCount = None

    try:
        sinceDays = int(args['--since'])
    except ( KeyError, TypeError):
        sinceDays = None

    
    try:
        showProgressBar = args['--no-progress-bar']
    except KeyError:
        showProgressBar = True
     
    # get the configuration file
    conf_file = args['CONFIGFILE']

    # get the destination directory
    dest_dir = args['DESTINATION']

    # read the config file and determine what to do
    config = configparser.ConfigParser()
    config.read(conf_file)

    try:
        twitconfig = config['twitter']
    except KeyError:
        log.exception('Twitter not configure')
        raise

    twit = Twitter( twitconfig )

    # get all the tweets
    # alltweets will be a dict of lists
    # each dict key is a followed twitter stream
    alltweets = twit.getAllTweets(sinceDays = sinceDays)

    # go through all the tweets and find any imagery
    flatten = lambda l: [item for sublist in l for item in sublist]
    
    # convert all tweets to a list if needed
    try:
        # assume a dictionary
        alltweets = flatten( alltweets.values() )
    except AttributeError:
        # assume it's a list
        pass

    if not maxCount:
        # if maxCount not set, use all tweets as max
        totlen = len(alltweets)
    elif len(alltweets) < maxCount:
        # if fewer tweets found than max count, use that number
        totlen = len(alltweets)
    else:
        # otherwise, process maxcCount at most            
        totlen = maxCount

    # if tweets are found, go through them
    if alltweets:
        for i,tweet in enumerate( alltweets ):

            # for each tweet, save the tweet as a json file
            jsonfile = os.path.sep.join( [ dest_dir,
                                           'tweet_' + tweet.id_str + '.json' ] )
            with open(jsonfile,'w') as f: json.dump( tweet._json , f )
            
            # and save the associated images
            #
            # check if there is an extended_entities attribute which will
            # specifiy multiple media
            try:
                entities = tweet.extended_entities
            except AttributeError:
                entities = tweet.entities

            # extract the media from the entities
            try:
                media = entities['media']
            except KeyError:
                # no media key present, so no media to match
                media = []

            for j,m in enumerate( media ):
                url = m['media_url']
                _, fext = os.path.splitext( url )
                
                medianame = os.path.sep.join( [ dest_dir,
                                                'tweet_' +
                                                tweet.id_str + '_' +
                                                str(j).rjust(3,'0') +
                                                fext ] )
                
                wget.download( url, medianame, bar = None )

            # count in progress_bar is i+1 because we start at zero and
            # this should not be zero-based counter
            if showProgressBar:
                progress_bar.print_progress(i+1,totlen)
                
            if i == totlen:
                break
