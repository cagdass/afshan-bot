#!/usr/bin/env python

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from time import time, sleep
import os, sys, types
import urllib2
import json
import string
from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)

host = 'localhost'
port = 27017
databaseName = 'afshanbot'

users = []
usernames = {}
links = []
user_links = {}
link = ''
canStop = False
b = ''

def u1():
    global users, usernames, user_links
    print 'u1()'
    for user in users:
        user_id = user['user_id']
        username = user['username']
        user_link = user['user_link']
        usernames[user_id] = username
        user_links[user_id] = user_link

def u2():
    global users, usernames, user_links
    print 'u2()'
    for key in usernames.keys():
        user = {}
        user['user_id'] = key
        user['username'] = usernames[key]
        if key in user_links.keys():
            user['user_link'] = user_links[key]
        users.append(user)

def getClient():
    global host, port
    client = MongoClient(host, port)
    return client

def update_dict(id, username):
    global usernames
    if id not in usernames:
        usernames[id] = username

def bs_source(url):
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')
    soup.prettify()

    return soup

def read_article(url):
    soup = bs_source(url)
    ps = soup.findAll('p')
    articles = []
    for p in ps:
        imgs = p.findAll('img')
        if len(imgs) > 0:
            for img in imgs:
                articles.append(img.get('src'))
        articles.append(p.text)
    print articles
    return articles

def check(soup):
    global links, link
    divs = soup.findAll('div', class_='block-item-big')
    for div in divs:
        imgs = div.findAll('img')
        for img in imgs:
            if 'afshan' in img.get('src'):
                a = div.find('a')
                l = a.get('href')
                if l not in links:
                    link = l
                    links.append(l)
                    break

def load():
    global users, usernames, links, user_links, link, databaseName
    client = getClient()
    db = client[databaseName]
    userCollection = db['users']
    linkCollection = db['links']

    cursor = userCollection.find()
    for doc in cursor:
        users.append(doc)

    cursor = linkCollection.find()
    for doc in cursor:
        link_ = doc['link']
        if link_ not in links:
            links.append(doc['link'])
    link = links[len(links)-1]

    client.close()
    u1()

def save(bot, update):
    global users, links, databaseName, usernames, user_links
    u2()

    client = getClient()
    db = client[databaseName]
    userCollection = db['users']
    linkCollection = db['links']

    print 'Saving'
    print usernames, user_links,
    print users, links

    for user in users:
        userCollection.update({'user_id': user['user_id']}, user, upsert=True)
    for link_ in links:
        linkCollection.update({'link': link_}, {'link': link_}, upsert=True)

    client.close()

def start(bot, update):
    global b, usernames, user_links, links
    i1 = update.message.chat_id
    i2 = update.message.from_user.username

    if i2 == 'cagdas':
        b = bot
        update.message.reply_text('Bot set')
        print 'Preload {} {} {}'.format(usernames,user_links,links)
        load()
        print 'Postload {} {} {}'.format(usernames,user_links,links)
        update.message.reply_text('Loaded')
    elif i2 == 'abdullahwali':
        message = 'Shut the fuck up Wali'
        update.message.reply_text(message)
    update_dict(i1,i2)
    add_user(i1)
    message = 'I\'m a Telegram Bot to update you whenever something new Afshan wrote is published\nSay /stop for me to stop.'
    update.message.reply_text(message)

def stop(bot, update):
    if update.message.from_user.username == 'cagdas':
        save()
        canStop = True
    else:
        i1 = update.message.chat_id
        remove_user(i1)
        update.message.reply_text('Sad to see you go.')

def add_user(id):
    global user_links
    if id not in user_links:
        user_links[id] = []

def remove_user(id):
    global user_links
    if id in user_links:
        del user_links[id]

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

def send_messages():
    global user_links, link, b
    if link and b:
        articles = read_article(link)
        for user in user_links:
            if link not in user_links[user]:
                try:
                    for i in xrange(len(articles)):
                        a = articles[i]
                        if a.encode('ascii', 'ignore'):
                            if 'http' not in a:
                                b.send_message(chat_id=user, text=a)
                            else:
                                b.send_photo(chat_id=user, photo=a)
                except BadRequest:
                    print 'Bad request'
                    pass
                except Unauthorized:
                    if user in usernames:
                        print '{}, {} blocked'.format(user, usernames[user])
                    else:
                        print '{} blocked'.format(user)

                user_links[user].append(link)

def main():
    global usernames,user_links,links,link,canStop

    with open('config.json') as config:
        c = json.load(config)
    token = c['token']
    updater = Updater(token)
    url = 'http://bilnews.bilkent.edu.tr/category/opinions/'

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("save", save))
    dp.add_handler(CommandHandler("stop", stop))

    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    while not canStop:
        print usernames
        print user_links
        print links
        print link
        print canStop
        soup = bs_source(url)
        check(soup)
        send_messages()
        sleep(60)

    updater.idle()

if __name__ == '__main__':
    main()
