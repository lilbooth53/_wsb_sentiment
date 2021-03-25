#function to get data from pushshift api
import numpy as np
import pandas as pd
import praw #reddit data api
import ffn #for loading financial data
import matplotlib.pyplot as plt
import seaborn as sn
import re #regex
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer #VADER sentiment model
import requests
import json
import csv
import time
import datetime
import tensorflow as tf
from tensorflow import keras


class run:
    def __init__(self):
        self.subStats = list()
        self.comments_by_day = list()
        self.scores = list()

    def getPushshiftData(self, query, after, before, sub):
        try: 
            url = 'https://api.pushshift.io/reddit/search/submission/?title='+str(query)+'&size=1000&after='+str(after)+'&before='+str(before)+'&subreddit='+str(sub)
            print(url)
            r = requests.get(url)
            data = json.loads(r.text)
            return data['data']
        except ValueError:
            print('JSON Decode Failed')
       

    #get relevant data from data extracted using previous function
    def collectSubData(self, subm):

        subData = [subm['id'], subm['title'], subm['url'], datetime.datetime.fromtimestamp(subm['created_utc']).date()]
    
        try:
            flair = subm['link_flair_text']
        except KeyError:
            flair = "NaN"
        subData.append(flair)
        self.subStats.append(subData)
        

    def reddit_api(self, df_1):
        #collect comments using praw
        reddit = praw.Reddit(client_id='WenzxF-VwYwdIg', client_secret='6xjTW0jhSrGs9i75UNA2nfnmnkvz4A', user_agent='Arjun')
    
        for url in df_1['url'].tolist():
            print("HELO")
            try:
                submission = reddit.submission(url=url)
                submission.comments.replace_more(limit=0)
                comments=list([(comment.body) for comment in submission.comments])
            except:
                comments=None
            self.comments_by_day.append(comments)
        return df_1

    def sentiment(self, df_1):
        
        analyser = SentimentIntensityAnalyzer()
       
        c = list()
        for comments in self.comments_by_day:
            sentiment_score=0
            try:
                for comment in comments:
                    sentiment_score=sentiment_score+analyser.polarity_scores(comment)['compound']
                  

            except TypeError:
                sentiment_score=0
      
            self.scores.append(sentiment_score)
            c.append(comments)
        df_1['sentiment score']=self.scores

        df_1['text']=c

        return df_1


    def full_query(self,  sub='wallstreetbets',  before = "1616621265", after = "1420070400", query = "Daily Discussion Thread"):
        sub = sub='wallstreetbets'
        subCount = 0
        

        # First Function Call
        data = self.getPushshiftData(query, after, before, sub)


        # Will run until all posts have been gathered 
        # from the 'after' date up until before date
        try: 
            while len(data) > 0:
                for submission in data: 
                    # Second function call
                    self.collectSubData(subm = submission)
                    subCount+=1
                # Calls getPushshiftData() with the created date of the last submission
                print(len(data))
                print(str(datetime.datetime.fromtimestamp(data[-1]['created_utc'])))
                after = data[-1]['created_utc']
                data = self.getPushshiftData(query, after, before, sub)
        except TypeError: 
            pass

        #organize data into dataframe
        data=dict()
        ids=list()
        titles=list()
        urls=list()
        dates=list()
        flairs=list()

        for stat in self.subStats:
            ids.append(stat[0])
            titles.append(stat[1])
            urls.append(stat[2])
            dates.append(stat[3])
            flairs.append(stat[4])
        data['id']=ids
        data['title']=titles
        data['url']=urls
        data['date']=dates
        data['flair']=flairs
        df_1=pd.DataFrame(data)
        df_1=df_1[df_1['flair']=='Daily Discussion']

        df_1 = self.reddit_api(df_1)
        df_1 = self.sentiment(df_1)
        print(df_1)
       # df_1.to_excel('first.xlsx',)

