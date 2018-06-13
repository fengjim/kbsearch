from dateutil.parser import parse
from datetime import datetime
from threadworker import ThreadWorker

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import sys
import os.path
import inspect
import argparse
import mechanize
import yaml

DEFAULT_CONFIG_FILE = 'config.yaml'
DEFAULT_NUM_OF_THREADS = 6
DEFAULT_CLOUDPHYSICS_LOGIN_ADDRESS = 'https://app.cloudphysics.com/login'
DEFAULT_CLOUDPHYSICS_KBLIST_CSV_ADDRESS = 'https://app.cloudphysics.com/issuesalert/entries/csv'
CLOUDPHYSICS_LOGIN_UI_USERNAME_ID = 'username'
CLOUDPHYSICS_LOGIN_UI_PASSWORD_ID = 'password'

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
    br[CLOUDPHYSICS_LOGIN_UI_USERNAME_ID] = username
    br[CLOUDPHYSICS_LOGIN_UI_PASSWORD_ID] = password

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

def createDriver(driver, path):

    if driver == 'chrome':
        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(path, chrome_options=chrome_options)
        return driver

    return None

def destroyDriver(driver, instance):
    if driver == 'chrome':
        instance.quit()

def startWorkers(threadNum, lines, indices, driver, path):
    # calculate the range of KBs each threadworker should handle
    slotsize = len(lines) / threadNum
    leftover = len(lines) % threadNum
    workers = []
    driverInstances = []
    for slot in range(threadNum + 1 if leftover > 0 else threadNum):
        drInst = createDriver(driver, path)
        driverInstances.append(drInst)
        sIndex = slotsize*slot
        eIndex = len(lines) - 1 if sIndex + slotsize > len(lines) else sIndex + slotsize - 1
        worker = ThreadWorker(driver = drInst, wlist = lines, sIndex = sIndex, eIndex = eIndex,
                    indices = indices)
        workers.append(worker)
        worker.start()

    for worker in workers:
        worker.join()

    for di in drivers:
        destroyDriver(driver, di)

if len(sys.argv) > 1:
    configFile = sys.argv[1]
else:
    scriptDir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    configFile = os.path.join(scriptDir, DEFAULT_CONFIG_FILE)


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

driverCfg = cfg.get('driver')
if driverCfg is not None:
    driver = driverCfg.get('driver', 'chrome')
    path = driverCfg.get('driver_path', '/usr/lib/chromium-browser/chromedriver')
else:
    driver = 'chrome'
    path = '/usr/lib/chromium-browser/chromedriver'

startWorkers(cpCfg.get('threads', DEFAULT_NUM_OF_THREADS), lines, columnIndices, driver, path)

print 'finished all the KB scanning at', datetime.now().strftime('%Y %m %d %H:%M:%S:%f')
