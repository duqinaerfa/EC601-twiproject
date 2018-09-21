import tweepy
from tweepy import OAuthHandler
import json
import os
import urllib.request
import io

consumer_key = "nOtk4Opwok3qmKEaXC62CPX5x"
consumer_secret = "qb7d5RhOTgYviTeNOEMNf8cV0WXXRUbPLbFbIqxn5xaYRitDvf"
access_token = "1039252091238268930-tOd5tJBIXFg2vSh3b11VcOITMs1tHG"
access_secret = "bQUVnQJkhKwKKJ6QJbYwCgWYnQ3ES15eKIAm1hMwzHC87"


@classmethod
def parse(cls, api, raw):
    status = cls.first_parse(api, raw)
    setattr(status, 'json', json.dumps(raw))
    return status


# Status() is the data model for a tweet
tweepy.models.Status.first_parse = tweepy.models.Status.parse
tweepy.models.Status.parse = parse
# User() is the data model for a user profil
tweepy.models.User.first_parse = tweepy.models.User.parse
tweepy.models.User.parse = parse
# You need to do it for all the models you need

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)

tweets = api.user_timeline(screen_name='TreaclyR',
                           count=200, include_rts=False,
                           exclude_replies=True)

last_id = tweets[-1].id

while (True):
    more_tweets = api.user_timeline(screen_name='TreaclyR',
                                    count=200,
                                    include_rts=False,
                                    exclude_replies=True,
                                    max_id=last_id - 1)
    # There are no more tweets
    if (len(more_tweets) == 0):
        break
    else:
        last_id = more_tweets[-1].id - 1
        tweets = tweets + more_tweets

media_files = set()
for status in tweets:
    media = status.entities.get('media', [])
    if(len(media) > 0):
        media_files.add(media[0]['media_url'])

num=0
for media_file in media_files:
    save_name = 'img%03d.jpg'%num
    urllib.request.urlretrieve(media_file,save_name)
    num = num + 1