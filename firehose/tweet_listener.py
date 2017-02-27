import cPickle
import datetime
import json
import os
import random
import sys
import time
import traceback

from profanity import profanity
import requests
import tweepy

from helper_functions import connect_redis_db, get_raw_tweets_sample_from_url

# connect to redis
r = connect_redis_db()

# twitter compute URL, from manifest
#SENTIMENT_COMPUTE_URL=os.getenv('SENTIMENT_COMPUTE_URL',None)
RAW_TWEET_STREAM_CHANNEL = os.getenv('RAW_TWEET_STREAM_CHANNEL',None)
if not RAW_TWEET_STREAM_CHANNEL:
    sys.stderr.write('{}\n'.format(
        "Missing redis channel name to write twitter feed"
    ))


# connect to twitter api
CONSUMER_KEY = os.getenv('CONSUMER_KEY',None)
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET',None)
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN',None)
ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET',None)
if not all((CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)):
    sys.stderr.write('{}\n'.format(
        "Missing Twitter credentials in environment variables."
    ))
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)
terms = ['tesla', 'microsoft', 'apple', 'lenovo', 'samsung']

# load synthetic tweets for backup
sample_tweets_url = 'https://github.com/scottcode/consumer-desire-twitter-model/raw/master/teslatweet_2017-1-5.gz'
syn_tweets = get_raw_tweets_sample_from_url(sample_tweets_url)

class CustomStreamListener(tweepy.StreamListener):

    """Source: http://www.brettdangerfield.com/post/realtime_data_tag_cloud/ """
    def __init__(self, api):
        self.api = api
        self.tweet_list = []
        self.score_tweet_time = time.time()
        self.write_to_redis_time = time.time()
        self.write_to_redis_int = 10
        super(tweepy.StreamListener, self).__init__()

    def save_posted_tweet_to_redis(self, tweet, source):
        msg = json.dumps({'text': profanity.censor(tweet['text']),  # for public dashboard
                          'source': source})
        r.publish(RAW_TWEET_STREAM_CHANNEL, msg)

    def english_tweet(self, tweet):
        return tweet.lang == 'en'

    def emulate_tweet(self):
        '''Send a fake tweet using previously saved tweets'''
        # hack
        self.on_status(random.choice(syn_tweets), source = 'emulated')

    def on_status(self, status, source = 'live'):
        global full_tweet
        global cur_tweet
        #global cur_p

        full_tweet = status
        del_time = full_tweet.created_at - datetime.datetime.utcnow()
        # print del_time.total_seconds()
        if not self.english_tweet(status):
            return
        # print status.text
        self.tweet_list.append(status._json)
        time_since_last_score = (time.time() - self.score_tweet_time)


        time_since_last_redis_write = (time.time() - self.write_to_redis_time)
        
        if time_since_last_redis_write > self.write_to_redis_int:
            cur_tweet = self.tweet_list[-1]
            self.save_posted_tweet_to_redis(cur_tweet,source)

            self.tweet_list = []


    def on_error(self, status_code):
        print >> sys.stderr, 'Encountered error with status code:', status_code
        return True  # Don't kill the stream

    def on_timeout(self):
        print >> sys.stderr, 'Timeout...'
        return True  # Don't kill the stream

stream = tweepy.streaming.Stream(auth, CustomStreamListener(api))
emulate_time = 60
while True:
    try:
        print 'Connecting to Twitter Firehose'
        stream.filter(track = terms, stall_warnings=True, filter_level="low")
    except KeyboardInterrupt:
        sys.stdout.write('{}\n'.format('Stopping due to KeyboardInterrupt'))
        break
    except Exception as e:
        print e
        sys.stderr.write(traceback.format_exc() + '\n')
        print 'Emulating tweets for {} seconds'.format(emulate_time)
        stream.disconnect()
        start_time = time.time()
        while (time.time() - start_time) < emulate_time:
            time.sleep(random.random())
            stream.listener.emulate_tweet()