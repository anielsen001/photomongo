"""
twitter inferface code
"""

import sys
import tweepy

class TwitterError(object):
    pass

class Twitter(object):

    consumer_key = None
    consumer_secret = None
    access_token = None
    access_token_secret = None

    feeds_to_follow = None

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
                  nToGet = sys.maxsize):
        """ 
        return tweets for screen name. currently get max possible which is
        3240. 
        Modeled after: https://gist.github.com/yanofsky/5436496

        nToGet is the number to return, (default) means get max tweets, in practice,
        limited by twitter's max of 3240

        returns a list of all the tweets

        later, added tweets since date, other options
        """

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

        print('Got ' + str(len(new_tweets)) + ' tweets ...')
        
        if len(new_tweets) == 0:
            # nothng returned - return empty list
            return new_tweets

        alltweets.extend(new_tweets)
        
        oldest = new_tweets[-1].id - 1
        #nToGet -= nThisTime
        nGot += nThisTime
        
        while nGot < nToGet:
            # keep getting tweets until we have the number we want

            # how many to get this time?
            nThisTime = nPerTry if (nToGet - nGot) > nPerTry else (nToGet - nGot)
            print(nThisTime)
            print(nToGet)
            print(nGot)
            
            new_tweets = self.api.user_timeline(screen_name = screen_name,
                                                count = nThisTime,
                                                max_id = oldest,
                                                include_rts = True,
                                                tweet_mode='extended')

            print('Got ' + str(len(new_tweets)) + ' tweets ...')
                    
            
            # if no tweets retuned, then we got the most
            if len(new_tweets) == 0: break
            
            # need to keep track of max_id and look for older id's
            oldest = new_tweets[-1].id - 1
            
            nGot += len(new_tweets)

            alltweets.extend(new_tweets)

        return alltweets
    
    def getAllTweets(self):
        """
        get all the tweets possible for the current configuration

        may take a while
        """

        alltweets=[]
        
        # loop over all the feeds in feeds_to_follow
        for feed in self.feeds_to_follow:
            feedtweets = self.getTweets(feed)
            alltweets.extend(feedtweets)

        return alltweets
