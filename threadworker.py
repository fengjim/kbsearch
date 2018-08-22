import threading

from dateutil.parser import parse
from datetime import datetime, date

kbformat = '{updatetype};{kburl};{cpdate};{kbdate};{author};{detail}'
hyperlinkformat = '=HYPERLINK("{url}")'
waiting_time = 10
dateformat = '%Y-%m-%d'
KB_VENDOR_VMWARE = 'VMware'

class ThreadWorker(threading.Thread):

    def __init__(self, driver, wlist = [], sIndex = 0, eIndex = 0, indices = {}, logger = None):
        threading.Thread.__init__(self)
        self.workingList = wlist
        self.startIndex = sIndex
        self.endIndex = eIndex
        self.indices = indices
        self.driver = driver
        self.driver.implicitly_wait(waiting_time)
        self.logger = logger

    def __del__(self): pass

    def __log(self, kb):
        if self.logger:
            self.logger.log(kb)
        else:
            print(kb)

    def __hyperlink(self, url):
        return hyperlinkformat.format(url = url)

    def __get_date(self):
        """
            an example document structure looks like:
            <div class="articleInfo" data-aura-rendered-by="346:5;a">
                <h1 class="articleInfoTitle" data-aura-rendered-by="347:5;a">Info</h1>
                <p class="articleInfoContent" data-aura-rendered-by="41:197;a">
                    <span data-aura-rendered-by="42:197;a">
                        <b data-aura-rendered-by="43:197;a">Created: </b>
                    </span>
                    <lightning-formatted-date-time data-aura-rendered-by="45:197;a">2008-11-26</lightning-formatted-date-time>
                    <!--render facet: 46:197;a-->
                </p>
                <p class="articleInfoContent" data-aura-rendered-by="47:197;a">
                    <span data-aura-rendered-by="48:197;a">
                        <b data-aura-rendered-by="49:197;a">Last Updated: </b>
                    </span>
                    <lightning-formatted-date-time data-aura-rendered-by="51:197;a">2017-9-5</lightning-formatted-date-time>
                    <!--render facet: 52:197;a-->
                </p>
                <p class="articleInfoContent" data-aura-rendered-by="351:5;a">
                    <span data-aura-rendered-by="352:5;a">
                        <b data-aura-rendered-by="353:5;a">Total Views: </b>
                    </span>
                    <span data-aura-rendered-by="357:5;a" class="uiOutputNumber" data-aura-class="uiOutputNumber">5,068</span>
                </p>
                <!--render facet: 358:5;a--><!--render facet: 359:5;a-->
            </div>

        """
        # better/smarter way to locate the element?
        articleInfoList = self.driver.find_elements_by_class_name('articleInfo')
        for articleInfo in articleInfoList:
            infoType = articleInfo.find_element_by_class_name('articleInfoTitle')
            if infoType and 'Info' == infoType.text.strip():
                contentList = articleInfo.find_elements_by_class_name('articleInfoContent')
                for content in contentList:
                    b_tag = content.find_element_by_tag_name('b')
                    if b_tag and 'Last Updated:' == b_tag.text.strip():
                        update_time_tag = content.find_element_by_tag_name('lightning-formatted-date-time')
                        if update_time_tag:
                            return update_time_tag.text

        return None

    def __checkb(self, url, cpupdate, author):
        cpdate = date.today()
        try:
            cpdate = parse(cpupdate)
        except Exception as ex:
            self.__log(kbformat.format(updatetype='date_error',
                kburl=self.__hyperlink(url),
                cpdate=cpupdate,
                kbdate='unknown',
                author=author,
                detail=ex.args))
            return
        try:
            self.driver.get(url)
        except Exception as ex:
            self.__log(kbformat.format(updatetype='page_load_error',
                kburl=self.__hyperlink(url),
                cpdate=cpupdate,
                kbdate='unknown',
                author=author,
                detail=ex.args))
            return

        date_str = self.__get_date()
        if date_str:
            try:
                kbdate = parse(date_str)
                if kbdate > cpdate:
                    self.__log(kbformat.format(updatetype='update',
                        kburl=self.__hyperlink(url),
                        cpdate=cpdate.strftime(dateformat),
                        kbdate=kbdate.strftime(dateformat),
                        author=author,
                        detail=''))
                elif kbdate < cpdate:
                    self.__log(kbformat.format(updatetype='data_lost',
                        kburl=self.__hyperlink(url),
                        cpdate=cpdate.strftime(dateformat),
                        kbdate=kbdate.strftime(dateformat),
                        author=author,
                        detail=''))
            except Exception as ex:
                self.__log(kbformat.format(updatetype='date_error',
                    kburl=self.__hyperlink(url),
                    cpdate=cpdate.strftime(dateformat),
                    kbdate='unknow',
                    author=author,
                    detail=ex.args))
        else :
            self.__log(kbformat.format(updatetype='no_date_on_page_error',
                kburl=self.__hyperlink(url),
                cpdate=cpdate.strftime(dateformat),
                kbdate='unknow',
                author=author,
                detail='no update date found'))

    def run(self):
        for kb in self.workingList[self.startIndex:self.endIndex]:
           attrs = kb.split('|')
           if len(attrs) > self.indices['publisher_index']  \
                and attrs[self.indices['publisher_index']].strip() == KB_VENDOR_VMWARE :
                self.__checkb(attrs[self.indices['url_index']].strip(),
                            attrs[self.indices['last_update_index']].strip(),
                            attrs[self.indices['submitter_index']].strip())
