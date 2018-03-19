#!/usr/bin/env python
"""
photomongo - read and process all tweets possible

Usage:
  photomongo CONFIGFILE

Options:
  -h --help  Show this screen. 

"""

import os, sys
from docopt import docopt

import configparser

from searcher import Searcher
import searcher
from twitter import Twitter

if __name__=='__main__':
    
    args = docopt(__doc__)

    # get the configuration file
    conf_file = args['CONFIGFILE']

    # read the config file and determine what to do
    config = configparser.ConfigParser()
    config.read(conf_file)

    # require a 'search' section in the config file know what to search fo
    try:
        searchconf = config['search']
    except KeyError:
        print('Search configuration parameters not configured')
        raise

    # require a twitter configuration
    try:
        twitconfig = config['twitter']
    except KeyError:
        print('Twitter not configured')
        raise
    
    twit = Twitter(twitconfig)

    # get all the tweets
    alltweets = twit.getAllTweets()
        
    # set up to search the tweets
    tweetsearcher = searcher.TweetSearcher(searchconf)

    # search all the tweets
    for tweet in alltweets:
        tweetsearcher.searchTweet(tweet)
    
