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
  --since=<days>  maximum number of days to get in the past

"""

import sys
import logging
logging.basicConfig(level=logging.DEBUG,
                    handlers = [logging.FileHandler('photomongo.log')] ) 

log = logging.getLogger(__name__)

import os
from docopt import docopt
import configparser
import json

import searcher
from twitter import Twitter
from gmail import Gmail
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
    except ( KeyError, TypeError ):
        maxCount = None

    try:
        sinceDays = int(args['--since'])
    except ( KeyError, TypeError):
        sinceDays = None
        
    log.debug('pickleToFile = ' + str(pickleToFile))
    log.debug('pickleFromFile = ' + str(pickleFromFile))
        
    # get the configuration file
    conf_file = args['CONFIGFILE']

    # read the config file and determine what to do
    config = configparser.ConfigParser()
    config.read(conf_file)

    # check if gmail is configured
    try:
        gmailconf = config['gmail']
    except KeyError:
        # gmail not configured
        log.info('gmail not configured, emails will not be sent')

    try:
        gm = Gmail(gmailconf)
        log.info('gmail configured')
    except:
        # gmail configuration error
        log.error('gmail configuration error')
        raise
        
    # require a 'search' section in the config file know what to search fo
    try:
        searchconf = config['search']
    except KeyError:
        log.exception('Search configuration parameters not configured')
        raise

    # check if configured to write out save file
    try:
        results_save_file = searchconf['save results file']
        log.info('Will save search results to: ' + results_save_file)
    except KeyError:
        results_save_file = None
        log.info('No configured file for search results')


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
        alltweets = twit.getAllTweets(sinceDays = sinceDays)
        #alltweets = twit.getAllTweets()

    print(len(alltweets))
        
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

    # convert all tweets to a list if needed
    try:
        # assume a dictionary
        alltweets = flatten( alltweets.values() )
    except AttributeError:
        # assume it's a list
        pass

    
    if not maxCount:
        # if maxCount not set, use all tweets at max
        totlen = len(alltweets)
    elif len(alltweets) < maxCount:
        # if fewer tweets found than max count, use that number
        totlen = len(alltweets)
    else:
        # otherwise, process maxcCount at most            
        totlen = maxCount

    print(totlen)
    searchresults = []
    
    for i,tweet in enumerate( alltweets ):
        # this searches on tweet at a time
        searchresults.extend( tweetsearcher.searchTweet(tweet) )
        progress_bar.print_progress(i,totlen-1)
        if i == totlen: break

    # send email if search results come back
    if searchresults:
        gm.create_and_send_message('photomongo results to review',\
                                   'found results')
    else:
        msg = 'Photomongo found no results in ' + str(totlen) + ' tweets.'
        gm.create_and_send_message('photomongo no results',\
                                   msg)

            
