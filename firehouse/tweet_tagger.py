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
pubsub = r.pubsub()
pubsub.subscribe(CHANNEL)

def tag_tweet(tweet_text):
    """
    Capture the tweet text published to redis and run through the google nlp API
    """
    url = '{}/nlp'.format(TWEET_TAG_URL)
    result = requests.post(url, data=json.dumps({"content": tweet_text}))
    return result.text



while True:
    try:
        print('Listening to {channel}'.format(channel=CHANNEL))
        for item in pubsub.listen():
            data = item['data']
            try:
                text = json.loads(data)['text']
                print(text)
                response = tag_tweet(text)
                print("Google nlp response:\n")
                print(response)
            except:
                print("No text found")
    except KeyboardInterrupt:
        sys.stdout.write('{}\n'.format('Stopping due to KeyboardInterrupt'))
        break
