from dateutil.parser import parse
from datetime import datetime
from threadworker import ThreadWorker

import sys
import os.path
import mechanize
import yaml
import argparse

DEFAULT_NUM_OF_THREADS = 6
DEFAULT_CLOUDPHYSICS_LOGIN_ADDRESS = 'https://app.cloudphysics.com/login'
DEFAULT_CLOUDPHYSICS_KBLIST_CSV_ADDRESS = 'https://app.cloudphysics.com/issuesalert/entries/csv'
KB_URL_COL = 'url'
KB_LAST_UPATE_COL = 'last_updated_date'
KB_SUBMITTER_COL = 'submitted_by'
KB_PUBLISHER_COL = 'publisher'

def getCSV(cplogin, username, password, cpcsv):
    # setup the broswer
    br = mechanize.Browser()
    br.set_handle_robots(False)

    br.addheaders = [("User-agent","Mozilla/5.0 (X11 U Linux i686 en-US rv:1.9.2.13) \
                            Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13")]

    signInPage = br.open(cplogin)  #the login url
    br.select_form(nr = 0)
    br["username"] = username
    br["password"] = password

    loggedIn = br.submit()
    if loggedIn.code != 200:
        print 'failed to login cloudphysics'
        return ''
    csvpage = br.open(cpcsv)

    if csvpage.code != 200:
        print 'failed to open CSV file'
        return ''
    csvfile = csvpage.read()
    br.close()
    return csvfile

def parseColumnIndex(indices, header):

    url_index = -1
    last_update_index = -1
    submitter_index = -1
    publisher_index = -1

    for index, column in enumerate(header.split('|')):
        if column == KB_PUBLISHER_COL:
            publisher_index = index
        elif column == KB_URL_COL:
            url_index = index
        elif column == KB_LAST_UPATE_COL:
            last_update_index = index
        elif column == KB_SUBMITTER_COL:
            submitter_index = index
    if url_index == -1 or last_update_index == -1 or submitter_index == -1 or publisher_index == -1 :
        print 'failed to parse header line in CSV file'
        print url_index, last_update_index, submitter_index, publisher_index
        return False

    indices['publisher_index'] = publisher_index
    indices['url_index'] = url_index
    indices['last_update_index'] = last_update_index
    indices['submitter_index'] = submitter_index

    return True

def startWorkers(threadNum, lines, indices, phantomjs):
    # calculate the range of KBs each threadworker should handle
    slotsize = len(lines) / threadNum
    leftover = len(lines) % threadNum
    workers = []
    for slot in range(threadNum + 1 if leftover > 0 else threadNum):
        sIndex = slotsize*slot
        eIndex = len(lines) - 1 if sIndex + slotsize > len(lines) else sIndex + slotsize - 1
        worker = ThreadWorker(wlist = lines, sIndex = sIndex, eIndex = eIndex,
                    indices = indices, phantomjs = phantomjs)
        workers.append(worker)
        worker.start()

    for worker in workers:
        worker.join()

configFile = './config.yaml'
if len(sys.argv) > 1:
    configFile = sys.argv[1]

# check config file exists or not
if not os.path.isfile(configFile):
    print 'config file ', configFile, 'does not exist'
    exit(1)

with open(configFile, 'r') as ymlFile:
    cfg = yaml.load(ymlFile)

cpCfg = cfg.get('cloudphysics', {})
cpLoginPage = cpCfg.get('login_page', DEFAULT_CLOUDPHYSICS_LOGIN_ADDRESS)
cpCSVPage = cpCfg.get('kblist_page', DEFAULT_CLOUDPHYSICS_KBLIST_CSV_ADDRESS)
username = cpCfg.get('username')
password = cpCfg.get('password')
phantomjs = cfg.get('phantomjs', '')

if not username or not password:
    print 'failed to read cloudphysics login information'
    exit(1)

print 'Scanning Script started at', datetime.now().strftime('%Y %m %d %H:%M:%S:%f')
csvfile = getCSV(cpLoginPage, username, password, cpCSVPage)
if not csvfile:
    print 'Cloudphysics KB list is empty'
    exit(1)

lines = csvfile.split('\n')
if len(lines) <= 0 :
    print 'unable to parse csv file'
    exit(1)

print 'CSV file from Cloudphysics with', len(lines), 'lines'

columnIndices = {}
if not parseColumnIndex(columnIndices, lines[0]):
    exit(1)

startWorkers(cpCfg.get('threads', DEFAULT_NUM_OF_THREADS), lines, columnIndices, phantomjs)

print 'finished all the KB scanning at', datetime.now().strftime('%Y %m %d %H:%M:%S:%f')
