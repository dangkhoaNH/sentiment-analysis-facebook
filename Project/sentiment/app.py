import streamlit as st
import pandas as pd
import numpy as np
import regex as re
import emoji
import string
from underthesea import word_tokenize
from underthesea import sentiment

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.svm import SVC
import numpy as np
import nltk
import re
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.preprocessing import MaxAbsScaler
from sklearn.svm import LinearSVC
import joblib

import streamlit as st
import matplotlib.pyplot as plt

from time import sleep

from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

st.title('Phân tích cảm xúc từ bài viết Facebook')

# Link FB
title = st.text_input('Link')

#Create dictionary for posts and comments
posts = dict()
comments = dict()

def initDriver():
    WINDOW_SIZE = "1920, 1080"
    chrome_options = Options()
    chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-blink-features=AutomationControllered")
    chrome_options.add_experimental_option('useAutomationExtension', False)
    prefs = {"profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--disable-dev-shm-usage")  # overcome limited resource problems
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument('disable-infobars')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def convertToCookie(cookie):
    try:
        new_cookie = ["c_user=", "xs="]
        cookie_arr = cookie.split(";")
        for i in cookie_arr:
            if i.__contains__('c_user='):
                new_cookie[0] = new_cookie[0] + (i.strip() + ";").split("c_user=")[1]
            if i.__contains__('xs='):
                new_cookie[1] = new_cookie[1] + (i.strip() + ";").split("xs=")[1]
                if (len(new_cookie[1].split("|"))):
                    new_cookie[1] = new_cookie[1].split("|")[0]
                if (";" not in new_cookie[1]):
                    new_cookie[1] = new_cookie[1] + ";"

        conv = new_cookie[0] + " " + new_cookie[1]
        if (conv.split(" ")[0] == "c_user="):
            return
        else:
            return conv
    except:
        print("Error Convert Cookie")

def loginFacebookByCookie(driver ,cookie):
    try:
        cookie = convertToCookie(cookie)
        print(cookie)
        if (cookie != None):
            script = 'javascript:void(function(){ function setCookie(t) { var list = t.split("; "); console.log(list); for (var i = list.length - 1; i >= 0; i--) { var cname = list[i].split("=")[0]; var cvalue = list[i].split("=")[1]; var d = new Date(); d.setTime(d.getTime() + (7*24*60*60*1000)); var expires = ";domain=.facebook.com;expires="+ d.toUTCString(); document.cookie = cname + "=" + cvalue + "; " + expires; } } function hex2a(hex) { var str = ""; for (var i = 0; i < hex.length; i += 2) { var v = parseInt(hex.substr(i, 2), 16); if (v) str += String.fromCharCode(v); } return str; } setCookie("' + cookie + '"); location.href = "https://mbasic.facebook.com"; })();'
            driver.execute_script(script)
            sleep(5)
    except:
        print("Error login")
    
def checkLiveClone(driver):
    try:
        driver.get("https://mbasic.facebook.com/")
        sleep(3)
        driver.get("https://mbasic.facebook.com/")
        sleep(3)
        elementLive = driver.find_elements(by=By.XPATH, value='//a[contains(@href, "/messages/")]')
        if (len(elementLive) > 0):
            print("Live")
            return True
        return False
    except:
        print("Error Check Live")

def loginFacebookByCookie(driver ,cookie):
    try:
        cookie = convertToCookie(cookie)
        if (cookie != None):
            script = 'javascript:void(function(){ function setCookie(t) { var list = t.split("; "); console.log(list); for (var i = list.length - 1; i >= 0; i--) { var cname = list[i].split("=")[0]; var cvalue = list[i].split("=")[1]; var d = new Date(); d.setTime(d.getTime() + (7*24*60*60*1000)); var expires = ";domain=.facebook.com;expires="+ d.toUTCString(); document.cookie = cname + "=" + cvalue + "; " + expires; } } function hex2a(hex) { var str = ""; for (var i = 0; i < hex.length; i += 2) { var v = parseInt(hex.substr(i, 2), 16); if (v) str += String.fromCharCode(v); } return str; } setCookie("' + cookie + '"); location.href = "https://mbasic.facebook.com"; })();'
            driver.execute_script(script)
            sleep(5)
    except:
        print("Error login")
        
def checkLiveCookie(driver, cookie):
    try:
        driver.get('https://mbasic.facebook.com/')
        sleep(3)
        driver.get('https://mbasic.facebook.com/')
        sleep(3)
        loginFacebookByCookie(driver ,cookie)

        return checkLiveClone(driver)
    except:
        print("Error Check Live")
        
def getCommentByPost(driver, postId, target = 500):
    try:
        driver.get(posts[postId])
        try:
            commentTags = driver.find_elements(by=By.XPATH, value='//div[contains(@data-sigil, "comment-body")]')
            if (len(commentTags) < target):
                nextButton = driver.find_elements(by=By.XPATH, value='//*[contains(@id,"see_next")]/a')
                if(len(nextButton)==1):
                    nextButton[0].click()
                    sleep(3)
                repliesButtons = driver.find_elements(by=By.XPATH, value='//a[contains(@href,"comment/replies/?ctoken=")]')
                while (len(repliesButtons) > 0):
                    for repliesButton in repliesButtons:
                        repliesButton.click()
                        sleep(3)
                    repliesButtons = driver.find_elements(by=By.XPATH, value='//a[contains(@href,"comment/replies/?ctoken=")]')
        except:
            print("Error")
        commentTags = driver.find_elements(by=By.XPATH, value='//div[contains(@data-sigil, "comment-body")]')
        if (len(commentTags)):
            for comment in commentTags:
                commentId = comment.get_attribute('data-commentid')
                if(commentId and len(comments) < target):
                    commentContent = comment.text
                    innerLinks = comment.find_elements(by=By.TAG_NAME, value='a')
                    if(len(innerLinks)):
                        for innerLink in innerLinks:
                            commentContent = commentContent.replace(innerLink.text, '')
                    comments[commentId] = commentContent
    except:
        print("Error")
        
def getPostsByFanpage(driver, pageId, amount):
    driver.get("https://touch.facebook.com/" + pageId)
    while len(posts) < amount:
        sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        shareButtons = driver.find_elements(by=By.XPATH, value='//a[contains(@href, "/sharer.php")]')
        if (len(shareButtons)):
            for shareButton  in shareButtons:
                postId = shareButton.get_attribute('href').split('sid=')[1].split('&')[0]
                commentButtons = driver.find_elements(by=By.XPATH, value='//a[contains(@data-click, "click_comment_ufi") and contains(@data-click, "'+str(postId)+'")]')
                if (len(commentButtons) == 1 and len(posts) < amount):
                    posts[postId] = commentButtons[0].get_attribute('href')

if (title != ""):
    
    # Crawl
    cookie = "c_user=100082982745987; xs=47%3A3rDjZrheBR82cA%3A2%3A1657434894%3A-1%3A-1;"
    driver = initDriver()
    isLive = checkLiveCookie(driver, cookie)
    if (isLive):
        getPostsByFanpage(driver, title[24:], 1)
        for postId in posts:
            getCommentByPost(driver, postId, 800)
    
    # len post equal = 1
    len(posts)
    
    # len(comments)
    len(comments)
    
    data = comments.values()
    len(data)
    
    df = pd.DataFrame(data, columns=['comment'])
    df.to_csv('comments-predict-app.csv')
    df = pd.read_csv('comments-predict-app.csv')
    
    # Delete index column
    df.drop(df.columns[[0]], axis=1, inplace=True)
    st.title('Bình luận')
    df
    
    # Process data crawl before model

    # Basic preprocessing as lower string
    def pre_processing(text):
        return text.str.lower()

    df['comment'] = pre_processing(df['comment'])

    # Delete NaN and empty row
    df = df[df.comment != '']
    df = df.dropna(subset=['comment'])
    df = df[df['comment'].apply(lambda comment: len(str(comment)) >= 5)]

    def remove_emoji(text):
        return emoji.get_emoji_regexp().sub("", text)

    df['comment'] = df['comment'].map(lambda comment: remove_emoji(comment))

    df['comment'] = df['comment'].map(lambda comment: comment.replace(string.punctuation,''))
    df['comment'] = df['comment'].map(lambda comment: comment.replace('_',' '))

    # Word segmentation
    df['segment'] = df['comment'].map(lambda comment: word_tokenize(comment))

    # Remove vietnamese stopwords - https://github.com/stopwords/vietnamese-stopwords

    # Read vietnamese stopwords file
    stopwords_df = pd.read_table('vietnamese-stopwords.txt')
    stopwords = stopwords_df.values.flatten()

    # Remove vietnamese stopwords function
    def remove_stopwords(segments):
        return [item for item in segments if item not in stopwords]

    df['segment'] = df['segment'].map(lambda segments: remove_stopwords(segments))

    def process(text):
        text = re.sub('&lt;/?.*?&gt;', ' &lt;&gt; ', str(text))
        text = re.sub('(\\d|\\W)+', ' ', str(text))
        return text

    df['segment'] = df['segment'].apply(lambda x: process(x))
    
    # Load vectorizer
    loaded_vectorizer_file = joblib.load('vectorizer_file.sav')
    
    # Load linearModel
    loaded_linearModel = joblib.load('linear_model.sav')
    
    output = loaded_linearModel.predict(loaded_vectorizer_file.transform(df['segment']))
    print(output)
    
    df.insert(2, "emotion", output)
    # df.drop("emotion", axis=1, inplace=True)
    
    # Load logisticModel
    loaded_logisticModel = joblib.load('logistic_model.sav')
    
    outputLogistic = loaded_logisticModel.predict(loaded_vectorizer_file.transform(df['segment']))
    print(outputLogistic)
    
    df.insert(3, "emotionLogistic", output)
    # df.drop("emotionLogistic", axis=1, inplace=True)
    st.title('Bình luận đã gán nhãn qua 2 mô hình')
    
    st.dataframe(df)
    
    counts = df['emotion'].value_counts().to_dict()
    st.title('Thống kê bình luận')
    st.write('Tích cực: ', counts['pos'])
    st.write('Trung tính: ', counts['neu'])
    st.write('Tiêu cực: ', counts['neg'])
    
    # st.title = pd.Series(df['emotion'].values).value_counts()
    
    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    st.title('Biểu đồ thống kê')
    total = counts['pos'] + counts['neu'] + counts['neg']
    labels = ['pos', 'neu', 'neg']
    sizes = [counts['pos'] / total, counts['neu'] / total, counts['neg'] / total]

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, explode = None, labels = labels, autopct='%1.1f%%',
            shadow = False, startangle = 90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    st.pyplot(fig1)

    
    
    
    