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
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)

usernames = {}
links = []
user_links = {}
link = ''
canStop = False
b = ''

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
    global usernames, links, user_links
    try:
        usernames = json.load(open('usernames.txt'))
    except ValueError:
        pass
    try:
        links = json.load(open('links.txt'))
    except ValueError:
        pass
    try:
        user_links = json.load(open('user_links.txt'))
    except ValueError:
        pass

def save():
    global usernames, links, user_links
    json.dump(usernames, open('usernames.txt', 'w'))
    json.dump(links, open('links.txt', 'w'))
    json.dump(user_links, open('user_links.txt', 'w'))

def start(bot, update):
    global b,usernames,user_links,links
    i1 = update.message.chat_id
    i2 = update.message.from_user.username
    update_dict(i1,i2)
    add_user(i1)
    if update.message.from_user.username == 'cagdas':
        b = bot
        update.message.reply_text('Bot set')
        print 'Preload {} {} {}'.format(usernames,user_links,links)
        load()
        print 'Postload {} {} {}'.format(usernames,user_links,links)
        update.message.reply_text('Loaded')
    elif update.message.from_user.username == 'abdullahwali':
        message = 'Shut the fuck up Wali'
        update.message.reply_text(message)
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
        save()

def remove_user(id):
    global user_links
    if id in user_links:
        del user_links[id]
        save()

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
                        if 'http' not in a:
                            b.send_message(chat_id=user, text=a)
                        else:
                            b.send_photo(chat_id=user, photo=a)
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
        sleep(10)

    updater.idle()

if __name__ == '__main__':
    main()
