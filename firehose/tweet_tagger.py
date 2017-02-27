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
    first_entity_str,
    get_text_entities,
    entity_to_str
)
#params
RAW_TWEET_STREAM_CHANNEL=os.getenv('RAW_TWEET_STREAM_CHANNEL',None)
if not RAW_TWEET_STREAM_CHANNEL:
    sys.stderr.write('{}\n'.format(
        "Missing redis channel name to write twitter feed"
    ))
TWEET_TAG_URL = 'http://127.0.0.1:5000'

r = connect_redis_db()

def tag_entities(tweet_text):
    """
    Capture the tweet text published to redis and run through the google nlp API
    """
    entities = get_text_entities(tweet_text)
    return entities

def listen_and_tag_entities(pubsub,channel):
    for item in pubsub.listen():
        try:
            data = json.loads(item['data'])
            text = data['text']
        except:
            print("invalid data: {}".format(data))
            text = ''
        entities = tag_entities(text)
        if entities:
            first_entity = entities[0]
            print(entity_to_str(first_entity))
        return entities


if __name__ == "__main__":
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(RAW_TWEET_STREAM_CHANNEL)
    print('Listening to {channel}'.format(channel=RAW_TWEET_STREAM_CHANNEL))
    while True:
        try:
            listen_and_tag_entities(pubsub=pubsub,channel=RAW_TWEET_STREAM_CHANNEL)
        except KeyboardInterrupt:
            sys.stdout.write('{}\n'.format('Stopping due to KeyboardInterrupt'))
            break
