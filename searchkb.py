from dateutil.parser import parse
from datetime import datetime

import mechanize

from threadworker import ThreadWorker

NUM_OF_THREADS = 6

print 'Scanning Script started at', datetime.now().strftime('%Y %m %d %H:%M:%S:%f')

# setup the broswer
br = mechanize.Browser()
br.set_handle_robots(False)

br.addheaders = [("User-agent","Mozilla/5.0 (X11 U Linux i686 en-US rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13")]


sign_in = br.open("https://app.cloudphysics.com/login")  #the login url
br.select_form(nr = 0)
br["username"] = 'wangguanlei.buaa@gmail.com'
br["password"] = "wangguanlei.buaa"

logged_in = br.submit()

logincheck = logged_in.read()

csvpage = br.open('https://app.cloudphysics.com/issuesalert/entries/csv')

csvfile = csvpage.read()

lines = csvfile.split('\n')

if len(lines) <= 0 :
    print 'unable to parse csv file'
    exit(1)

print 'CSV file from Cloudphysics with', len(lines), 'lines'

header = lines[0]

KB_URL_COL = 'url'
KB_LAST_UPATE_COL = 'last_updated_date'
KB_SUBMITTER_COL = 'submitted_by'
KB_PUBLISHER_COL = 'publisher'

kblist = []
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
    exit(1)
br.close()

# calculate the range of KBs each threadworker should handle
slotsize = len(lines) / NUM_OF_THREADS
leftover = len(lines) % NUM_OF_THREADS
workers = []
for slot in range(NUM_OF_THREADS + 1 if leftover > 0 else NUM_OF_THREADS):
    sIndex = slotsize*slot
    eIndex = len(lines) - 1 if sIndex + slotsize > len(lines) else sIndex + slotsize - 1
    worker = ThreadWorker(wlist = lines, sIndex = sIndex, eIndex = eIndex,
                indices = {'publisher_index': publisher_index,
                    'url_index':url_index,
                    'last_update_index': last_update_index,
                    'submitter_index': submitter_index})
    workers.append(worker)
    worker.start()

for worker in workers:
    worker.join()

print 'finished all the KB scanning at', datetime.now().strftime('%Y %m %d %H:%M:%S:%f')
