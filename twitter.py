"""
twitter inferface code
"""

import logging
log = logging.getLogger(__name__)

import sys
import tweepy

import datetime

class TwitterError(object):
    pass

class Twitter(object):

    consumer_key = None
    consumer_secret = None
    access_token = None
    access_token_secret = None

    feeds_to_follow = None

    max_per_feed = None
    
    # twitter api object
    api = None
    
    def __init__(self,twitter_dict):

        # these are the twitter tokens needed to connect
        self.consumer_key = twitter_dict['consumer key']
        self.consumer_secret = twitter_dict['consumer secret']
        self.access_token = twitter_dict['access token']
        self.access_token_secret = twitter_dict['access token secret']

        # open the twitter api
        self.openApi()
        
        # create a list of feeds to follow
        follow_str = twitter_dict['follow']
        follow_list = follow_str.strip().split()
        self.feeds_to_follow = follow_list

        # set default max to get per feed
        try:
            self.max_per_feed = int(twitter_dict['max per feed'])
        except KeyError:
            self.max_per_feed = sys.maxsize
            
    def openApi(self):
        """ open the twitter api """

        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret )
        auth.set_access_token( self.access_token, self.access_token_secret )
        api = tweepy.API(auth)
        self.api = api

    def getApi(self):
        # return the api for external use
        return self.api

    def getTweets(self,
                  screen_name,
                  nToGet = None,
                  start_date = None,
                  end_date = None):
        """ 
        return tweets for screen name. currently get max possible which is
        3240. 
        Modeled after: https://gist.github.com/yanofsky/5436496

        nToGet is the number to return, (default) means get max tweets, in practice,
        limited by twitter's max of 3240

        returns a list of all the tweets

        date time objects
        start_date = None - get tweets since the start date
        end_date = None - get tweets before the end date
        """

        if nToGet is None:
            nToGet = self.max_per_feed

        alltweets = [] # list to hold tweet
        nGot = 0 # number of tweets retrieved

        # only 200  tweets can be retrieved at a time
        nPerTry = 200

        # get the first batch of tweets
        nThisTime = nToGet if nToGet <= nPerTry else nPerTry
        new_tweets = self.api.user_timeline(screen_name = screen_name,
                                            count = nThisTime,
                                            include_rts = True,
                                            tweet_mode = 'extended' )

        if not start_date and not end_date:
            ret_tweets = new_tweets
        else:
            ret_tweets = []
            for _tweet in new_tweets:
                if _tweet.created_at >= start_date and\
                   _tweet.created_at <= end_date:
                    ret_tweets.append(_tweet)

        # loop over all the tweets and see if they fit with in the
        # requested time line
        
        
        log.debug('Got ' + str(len(new_tweets)) + ' tweets ...')
        
        if len(ret_tweets) == 0:
            # nothng returned - return empty list
            return ret_tweets

        alltweets.extend(ret_tweets)
        
        oldest = new_tweets[-1].id - 1
        #nToGet -= nThisTime
        nGot += nThisTime
        
        while nGot < nToGet:
            # keep getting tweets until we have the number we want

            # how many to get this time?
            nThisTime = nPerTry if (nToGet - nGot) > nPerTry else (nToGet - nGot)
            
            new_tweets = self.api.user_timeline(screen_name = screen_name,
                                                count = nThisTime,
                                                max_id = oldest,
                                                include_rts = True,
                                                tweet_mode='extended')

            log.debug('Got ' + str(len(new_tweets)) + ' tweets ...')
                    
            if not start_date and not end_date:
                ret_tweets = new_tweets
            else:
                ret_tweets = []
                for _tweet in new_tweets:
                    if _tweet.created_at >= start_date and\
                       _tweet.created_at <= end_date:
                        ret_tweets.append(_tweet)
            
            # if no tweets retuned, then we got the most
            if len(ret_tweets) == 0: break
            
            # need to keep track of max_id and look for older id's
            oldest = new_tweets[-1].id - 1
            
            nGot += len(new_tweets)

            alltweets.extend(ret_tweets)

        log.debug('Found ' + str(len(alltweets)) + ' tweets in ' + str(screen_name))
        return alltweets
    
    def getAllTweets(self,sinceDays=None):
        """
        get all the tweets possible for the current configuration

        may take a while
        """

        alltweets=[]

        if sinceDays:
            log.debug('Getting tweets since last ' + str(sinceDays) + ' days.')
            today = datetime.datetime.now()
            #enddate = today - datetime.timedelta(days= int(sinceDays) )
            start_date = today - datetime.timedelta( days= 7 )
        else:
            today = None
            start_date = None
            
        # loop over all the feeds in feeds_to_follow
        for feed in self.feeds_to_follow:
            feedtweets = self.getTweets(feed,
                                        start_date = start_date,
                                        end_date = today)
            alltweets.extend(feedtweets)

        return alltweets
