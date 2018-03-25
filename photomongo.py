#!/usr/bin/env python
"""
photomongo - read and process all tweets possible

Usage:
  photomongo [options] CONFIGFILE

Options:
  -h --help  Show this screen. 
  --pickle-to=<picklefile>  file to save tweets.
  --pickle-from=<picklefile>  file to read tweets.
  --max=<number>  maximum number to process, primarily for debug

"""

import sys
import logging
logging.basicConfig(level=logging.DEBUG,
                    handlers = [logging.FileHandler('photomongo.log')] ) 

log = logging.getLogger(__name__)


#fh = logging.FileHandler('photomongo.log')
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#fh.setFormatter(formatter)
#log.addHandler(fh)

import os
from docopt import docopt

import configparser

#from searcher import Searcher
import searcher
#searcher.log.addHandler(fh)

from twitter import Twitter
#from twitter import log as twitlog
#twitlog.addHandler(fh)



#from progress_bar import print_progress
import progress_bar


# to save/reload tweets use pickle
import pickle

if __name__=='__main__':
    
    args = docopt(__doc__)

    try:
        pickleFromFile = args['--pickle-from']
    except KeyError:
        pickleFromFile = None

    try:
        pickleToFile = args['--pickle-to']
    except KeyError:
        pickleToFile = None

    try:
        maxCount = int(args['--max'])
    except KeyError:
        maxCount = None

    log.debug('pickleToFile = ' + str(pickleToFile))
    log.debug('pickleFromFile = ' + str(pickleFromFile))
        
    # get the configuration file
    conf_file = args['CONFIGFILE']

    # read the config file and determine what to do
    config = configparser.ConfigParser()
    config.read(conf_file)

    # require a 'search' section in the config file know what to search fo
    try:
        searchconf = config['search']
    except KeyError:
        log.exception('Search configuration parameters not configured')
        raise

    # require a twitter configuration unless reading from an external file
    if pickleFromFile:
        # read tweets from pickle file instead of from twitter api
        with open(pickleFromFile,'rb') as f:
            alltweets = pickle.load(f)
    else:
        # read the tweets from twitter api directly
        try:
            twitconfig = config['twitter']
        except KeyError:
            log.exception('Twitter not configured')
            raise

        twit = Twitter(twitconfig)

        # get all the tweets
        # alltweets will be a dict of lists
        # each dict key is a followed twitter stream
        alltweets = twit.getAllTweets()

    # save the tweets if needed
    if pickleToFile:
        # write the tweets to a picklefile
        with open(pickleToFile,'wb') as f:
            pickle.dump(alltweets,f)
        
    # set up to search the tweets
    tweetsearcher = searcher.TweetSearcher(searchconf)
    
    # search all the tweets
    # https://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python
    flatten = lambda l: [item for sublist in l for item in sublist]

    if not maxCount:
        totlen=0
        for v in alltweets.values():
            totlen += len(v)
    else:
        totlen=maxCount

    searchresults = []
    for i,tweet in enumerate( flatten( alltweets.values() ) ):
        searchresults.extend( tweetsearcher.searchTweet(tweet) )
        progress_bar.print_progress(i,totlen)
        if i == totlen: break
