import json
import os
import time
import threading
import gzip
import requests
import StringIO

import redis
import tweepy


# initialize redis connection for local and CF deployment
def connect_redis_db(redis_service_name = 'p-redis'):
    #if os.environ.get('VCAP_SERVICES') is None: # running locally
    if  os.environ.get('LOCAL') is not None: #running locally
        DB_HOST = 'localhost'
        DB_PORT = 6379
        DB_PW = ''
        REDIS_DB = 1
    else:                                       # running on CF
        env_vars = os.environ['VCAP_SERVICES']
        print 'THIS IS THE SERVICE:', json.loads(env_vars)
        credentials = json.loads(env_vars)[redis_service_name][0]['credentials']
        DB_HOST = credentials['host']
        DB_PORT = credentials['port']
        DB_PW = credentials['password']
        REDIS_DB = 0

    return redis.StrictRedis(host=DB_HOST,
                              port=DB_PORT,
                              password=DB_PW,
                              db=REDIS_DB)


def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


def sse_pack(d):
    """For sending sse to client. Formats a dictionary into correct form for SSE"""
    buf = ''
    for k in ['retry','id','event','data']:
        if k in d.keys():
            buf += '{}: {}\n'.format(k, d[k])
    return buf + '\n'


def been_n_second(n,time_now,time_start,wait_time = 0.01):
    #TODO remove while loop and find better solution
    time_delta = time_now - time_start
    if time_delta >= n:
        return True
    # TODO remove time.sleep
    time.sleep(wait_time)
    return False


def raw_tweet_lines_to_status_objs(iterable):
    status_obj = tweepy.Status()
    return tuple(
        status_obj.parse(None, json.loads(line))
        for line in iterable
    )


def get_raw_tweets_sample(path='teslatweet_2017-1-16.gz'):
    """
    >>> get_raw_tweets_sample()[0].id > 0
    True
    """
    status_obj = tweepy.Status()
    with gzip.GzipFile(path) as f:
        statuses = raw_tweet_lines_to_status_objs(f.readlines())
    return statuses


def get_raw_tweets_sample_from_url(url):
    """
    >>> get_raw_tweets_sample_from_url('https://github.com/scottcode/consumer-desire-twitter-model/raw/master/teslatweet_2017-1-5.gz')[0].id > 0
    True
    """
    resp = requests.get(url)
    resp.raise_for_status()
    buff = StringIO.StringIO(resp.content)
    with gzip.GzipFile(fileobj=buff) as f:
        statuses = raw_tweet_lines_to_status_objs(f.readlines())
    return statuses