import tweepy
from tweepy import OAuthHandler
import json
import os
import urllib.request
import io
import pymysql
import pymongo
from datetime import datetime
from google.cloud import vision
from google.cloud.vision import types
from PIL import Image, ImageDraw, ImageFont

consumer_key = "nOtk4Opwok3qmKEaXC62CPX5x"
consumer_secret = "qb7d5RhOTgYviTeNOEMNf8cV0WXXRUbPLbFbIqxn5xaYRitDvf"
access_token = "1039252091238268930-tOd5tJBIXFg2vSh3b11VcOITMs1tHG"
access_secret = "bQUVnQJkhKwKKJ6QJbYwCgWYnQ3ES15eKIAm1hMwzHC87"

MYSQL_CONFIG = {
    'host' : '127.0.0.1',
    'port' : 3306,
    'user' : 'root',
    'password' : 'duqinmei19960204',
    'database' : 'twidatabase',
}


class myApi(object):
    def __init__(self):
        self.consumer_key = ''
        self.consumer_secret = ''
        self.access_key = ''
        self.access_secret = ''
        self.err = None
        # mysql
        try:
            self.mysql = pymysql.Connect(**MYSQL_CONFIG)
        except Exception as e:
            print('error: mysql connection fail')
            raise e
        # mongodb
        try:
            mongodb = pymongo.MongoClient('mongodb://localhost:27017')
            self.mongo = mongodb['twidatabase']
        except Exception as e:
            print('error: mongodb connection fail')
            raise e

    def set_consumer_key(self, c_key, c_secret):
        self.consumer_key = c_key
        self.consumer_secret = c_secret
        return 0

    def set_access_key(self, a_key, a_secret):
        self.access_key = a_key
        self.access_secret = a_secret
        return 0

    def connect(self):
        try:
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_secret)
            self.api = tweepy.API(auth)
        except Exception as e:
            self.error = e
            raise e
        finally:
            self.log('connect twitter')

    def getimages(self):
        tweets = self.api.user_timeline(screen_name='TreaclyR',
                                        count=20, include_rts=False,
                                        exclude_replies=True)

        last_id = tweets[-1].id
        while (True):
            more_tweets = self.api.user_timeline(screen_name='TreaclyR',
                                            count=20,
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

        self.log('download img%03d.jpg')

    def getvideo(self):
        os.popen('ffmpeg -r 0.5 -i img%03d.jpg -vf scale=500:500 -y -r 30 -t 60 out.mp4')
        self.log('convert to video')

    def label(self):
        # Instantiates a client
        client = vision.ImageAnnotatorClient()

        path = './'
        filelist = os.listdir(path)
        total_num = len(filelist)

        for file in filelist:
            if file.endswith('.jpg'):
                with io.open(file, 'rb') as image_file:
                    content = image_file.read()

                image = types.Image(content=content)

                response = client.label_detection(image=image)
                labels = response.label_annotations

                # Add label to image
                img = Image.open(file)
                draw = ImageDraw.Draw(img)

                # print(file)
                # print('Labels:')
                labelword = ''
                for label in labels:
                    labelword += str(label.description)+'\n'

                # print(labelword)
                (w, h) = img.size
                ttfont = ImageFont.truetype("/Library/Fonts/Arial.ttf", 30)
                draw.text((w/2-100, h/2-100), labelword, fill=(255, 255, 255), font=ttfont)
                img.save(file)

                userName = myApi.file_2_user(file)
                for l in labelword:
                    self.mysql_label(userName, l)
                    self.mongo_label(userName, l)

                self.log('get label of {} imgs'.format(total_num))


    @staticmethod
    def file_2_user(fname):
        index = fname.rfind('_')
        return fname[:index]


    def mysql_label(self, uname, label):
        sql = 'INSERT INTO twt_label(twtid, label, time) VALUES (%s,%s,%s)'
        try:
            with self.mysql.cursor() as cursor:
                cursor.execute(sql, (uname, label, datetime.now()))
        except Exception as e:
            self.err = e
            self.mysql_log()
            self.mysql.close()
            raise e


    def mongo_label(self, uname, label):
        try:
            labels = self.mongo['labels']
            cursor = labels.find({'userid': uname})

            count = 0
            for i in cursor:
                doc = i
                count += 1

            if count == 0:
                doc = {
                    'userid': uname,
                    'labels': [label],
                }
                labels.insert_one(doc)
            elif count == 1:
                assert isinstance(doc['labels'], list), 'doc[labels] not list'
                if label in doc['labels']:
                    return
                else:
                    doc['labels'].append(label)
                    new = {
                        '$set': {'labels': doc['labels']}
                    }
                    labels.update_one({'userid': uname}, new)
            else:
                raise Exception('error: count of uid in labels != 0 or 1')

        except Exception as e:
            self.err = e
            raise e


    def mysql_search(self, key):
        sql = 'SELECT twtid FROM twt_label WHERE label like "%{}%"'.format(key)
        try:
            with self.mysql.cursor() as cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
        except Exception as e:
            self.err = e
            self.mysql.close()
            raise e
        finally:
            self.log('search {} in mysql'.format(key))
        idlist = []
        for row in results:
            if not row[0] in idlist:
                idlist.append(row[0])
        return idlist


    def mongo_search(self, key):
        idlist = []
        try:
            labels = self.mongo['labels']
            for col in labels.find():
                assert isinstance(col['labels'], list), 'col[labels] not list'
                assert isinstance(col['userid'], str), 'col[userid] not str'
                if key in col['labels']:
                    if col['userid'] in idlist:
                        print('warning: more than one same userid in mongo[lanels]')
                    else:
                        idlist.append(col['userid'])
            return idlist
        except Exception as e:
            self.err = e
            raise e
        finally:
            self.log('search {} in mongodb'.format(key))


    def log(self, logstr='Unknown action'):
        self.mysql_log(logstr)
        self.mongo_log(logstr)


    def mysql_log(self, logstr='Unknown action'):
        if self.err:
            logstr = 'error: ' + str(self.err)

        sql = 'INSERT INTO twtapi_log(time, action) VALUES (%s, %s)'
        try:
            with self.mysql.cursor() as cursor:
                cursor.execute(sql, (datetime.now(), logstr))
            self.mysql.commit()
        except Exception as e:
            self.mysql.rollback()
            self.mysql.close()
            raise e


    def mongo_log(self, logstr='Unknown action'):
        if self.err:
            logstr = 'error: ' + str(self.err)

        doc = {
            'time': datetime.now(),
            'action': logstr,
        }
        try:
            log = self.mongo['log']
            log.insert_one(doc)
        except Exception as e:
            print('exception when write log into mongodb')
            raise e


    def mysql_total_log(self):
        sql = 'SELECT idtwtAPI_log FROM twtapi_log'
        try:
            with self.mysql.cursor() as cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
            return len(results)
        except Exception as e:
            self.err = e
            self.mysql.close()
            raise e
        finally:
            self.mysql_log('count total logs in mysql')


    def mongo_total_log(self):
        try:
            log = self.mongo['log']
            count = 0
            for i in log.find():
                count += 1
            return count
        except Exception as e:
            self.err = e
            raise e
        finally:
            self.mongo_log('count total logs in mongodb')


'''
CREATE TABLE `twidatabase`.`twi_label` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `twiid` VARCHAR(25) NULL,
  `label` VARCHAR(25) NULL,
  `time` DATETIME NULL,
  PRIMARY KEY (`id`));
'''


