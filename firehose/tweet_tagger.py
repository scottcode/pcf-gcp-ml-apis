from __future__ import print_function
"""
Subscribes to raw_tweet_stream in redis.  
Pushes tweets to google_api_service and publishes tags to redis
"""
import redis
from helper_functions import connect_redis_db
import sys
import requests
import json


#params
CHANNEL='raw_tweet_stream'
TWEET_TAG_URL = 'http://127.0.0.1:5000'

r = connect_redis_db()


def tag_tweet(tweet_text):
    """
    Capture the tweet text published to redis and run through the google nlp API
    """
    url = '{}/nlp'.format(TWEET_TAG_URL)
    result = requests.post(url, data=json.dumps({"content": tweet_text}))
    return result.text


def listen_and_tag(pubsub,channel):
    for item in pubsub.listen():
        data = item['data']
        try:
            text = json.loads(data)['text']
            print(text)
            response = tag_tweet(text)
            print("Google nlp response:\n")
            print(response)
            return response
        except:
            print("No text found")
            return None


if __name__ == "__main__":
    pubsub = r.pubsub()
    pubsub.subscribe(CHANNEL)
    print('Listening to {channel}'.format(channel=CHANNEL))
    while True:
        try:
            listen_and_tag(pubsub=pubsub,channel=CHANNEL)
        except KeyboardInterrupt:
            sys.stdout.write('{}\n'.format('Stopping due to KeyboardInterrupt'))
            break
