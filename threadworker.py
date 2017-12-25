import threading
import logging

from dateutil.parser import parse
from datetime import datetime, date
from selenium import webdriver

# create logger
logging.basicConfig(level=logging.INFO)
kbformat='{updatetype:10}; {kburl}; {cpdate}; {kbdate}; {author}; {detail}'
waiting_time = 10
dateformat = '%Y-%m-%d'
KB_VENDOR_VMWARE = 'VMware'

class ThreadWorker(threading.Thread):

    def __init__(self, wlist = [], sIndex = 0, eIndex = 0, indices = {}):
        threading.Thread.__init__(self)
        self.workingList = wlist
        self.startIndex = sIndex
        self.endIndex = eIndex
        self.indices = indices
        self.driver = webdriver.PhantomJS()
        self.driver.implicitly_wait(waiting_time)

    def __del__(self):
        self.driver.close()

    def __checkb(self, url, cpupdate, author):
        cpdate = date.today()
        try:
            cpdate = parse(cpupdate)
        except Exception as ex:
            print kbformat.format(updatetype='date_error',
                kburl=url,
                cpdate=cpupdate,
                kbdate='unknown',
                author=author,
                detail=ex.args)
            return

        self.driver.get(url)
        matches = self.driver.find_elements_by_class_name('uiOutputDate')
        if matches and len(matches) > 0:
            try:
                kbdate = parse(matches[0].text)
                if kbdate > cpdate or kbdate < cpdate:
                    print kbformat.format(updatetype='update',
                        kburl=url,
                        cpdate=cpdate.strftime(dateformat),
                        kbdate=kbdate.strftime(dateformat),
                        author=author,
                        detail='')
            except Exception as ex:
                print kbformat.format(updatetype='date_error',
                    kburl=url,
                    cpdate=cpdate.strftime(dateformat),
                    kbdate='unknow',
                    author=author,
                    detail=ex.args)
        else :
            print kbformat.format(updatetype='page_error',
                kburl=url,
                cpdate=cpdate.strftime(dateformat),
                kbdate='unknow',
                author=author,
                detail='no update date found')

    def run(self):
        for kb in self.workingList[self.startIndex:self.endIndex]:
           attrs = kb.split('|')
           if len(attrs) > self.indices['publisher_index']  \
                and attrs[self.indices['publisher_index']].strip() == KB_VENDOR_VMWARE :
               self.__checkb(attrs[self.indices['url_index']].strip(),
                            attrs[self.indices['last_update_index']].strip(),
                            attrs[self.indices['submitter_index']].strip())
