from __future__ import print_function
"""
Subscribes to raw_tweet_stream in redis.  
Pushes tweets to google_api_service and publishes info to redis
"""
import redis
from helper_functions import connect_redis_db
import sys
import json
import os
from google_api_helper_functions import (
    first_entity_str
)

def extract_data_from_message(message):
    """data is a redis message. Dict with keys: 'type', 'channel', 'pattern','data' """
    try:
        data = json.loads(message['data'])
    except:
        print("Invalid message: {}".format(message))
        data = None
    return data


#class to parse input redis data: data is the message content.  json with keys: 'source' & 'text' so far
class NLPAnalyzedTweet(object):
    """
    takes the raw data from an input message (a raw tweet) and returns NLP data from tweet.
    """
    def __init__(self,input_data):
        self.input_data = input_data
        self.tweet_text = input_data['text']
        self.first_entity_str = first_entity_str(self.tweet_text)
        self.output_data = json.dumps({'tweet_text':self.tweet_text,'first_entity_str':self.first_entity_str})

#Sublcass from custom generic parent class
#Want to subclass from this since we'll have multiple sources consuming the raw tiwtter stream- e.g. vision API and NLP api
class CustomStreamTagger(object):
    def __init__(self,r,listening_channel,publishing_channel):
        self.listening_channel=listening_channel
        self.publishing_channel=publishing_channel
        self.redis=r
        self.pubsub = r.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(self.listening_channel)

    def run(self):
        for message in self.pubsub.listen():
            print(message)
            #parse item, generate output data, save to redis
            message_data = extract_data_from_message(message)
            nlp_analyzed_tweet = NLPAnalyzedTweet(message_data)
            print(nlp_analyzed_tweet.first_entity_str)
            self.redis.publish(self.publishing_channel,nlp_analyzed_tweet.output_data)

if __name__ == "__main__":
    #params
    RAW_TWEET_STREAM_CHANNEL=os.getenv('RAW_TWEET_STREAM_CHANNEL',None)
    if not RAW_TWEET_STREAM_CHANNEL:
        sys.stderr.write('{}\n'.format(
            "Missing redis channel name to write twitter feed"
        ))

    TAGGED_TWEET_STREAM_CHANNEL=os.getenv('TAGGED_TWEET_STREAM_CHANNEL',None)
    if not TAGGED_TWEET_STREAM_CHANNEL:
        sys.stderr.write('{}\n'.format(
            "Missing redis channel name to write twitter feed"
        ))

    TWEET_TAG_URL = 'http://127.0.0.1:5000'

    r = connect_redis_db()


    nlp_tagger=CustomStreamTagger(r=r,
                                listening_channel=RAW_TWEET_STREAM_CHANNEL,
                                publishing_channel=TAGGED_TWEET_STREAM_CHANNEL
                                )
    print('Listening to channel: {channel}'.format(channel=RAW_TWEET_STREAM_CHANNEL))
    while True:
        try:
            nlp_tagger.run()
        except KeyboardInterrupt:
            sys.stdout.write('{}\n'.format('Stopping due to KeyboardInterrupt'))
            break
