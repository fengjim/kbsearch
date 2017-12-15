import re
from dateutil.parser import parse

import mechanize
from selenium import webdriver

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

print 'Get CSV file with', len(lines), 'lines'

header = lines[0]

KB_VENDOR_VMWARE = 'VMware'
KB_URL_COL = 'url'
KB_LAST_UPATE_COL = 'last_updated_date'
KB_SUBMITTER_COL = 'submitted_by'
KB_PUBLISHER_COL = 'publisher'

kblist = []
url_index = -1
last_update_index = -1
submitter_index = -1
publisher_index = -1

# non-greedy pattern
#regEx = re.compile('"uiOutputDate">(.+?)</span>')
dateformat = '%Y-%m-%d'


driver = webdriver.PhantomJS()
# implicity wait 5 seconds to let the page completely loaded
# todo: explicit wait is better to if login is needed or not
driver.implicitly_wait(6)

def checkb(br, url, cpupdate, author):
    #kbpage = br.open(url).read()
    # get kb update time
    #matches = regEx.findall(kbpage)
    driver.get(url)
    matches = driver.find_elements_by_class_name('uiOutputDate')
    if matches and len(matches) > 0:
        kbdate = parse(matches[0].text)
        cpdate = parse(cpupdate)
        if kbdate > cpdate or kbdate < cpdate:
            print 'update;', url, ';', cpdate.strftime(dateformat), ';', kbdate.strftime(dateformat), ';', author
    else :
        print 'error;', url, ';', cpupdate, ';', 'unknown', ';', author

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

for kb in lines[1:]:
   attrs = kb.split('|')
   if len(attrs) > publisher_index and attrs[publisher_index].strip() == KB_VENDOR_VMWARE :
       checkb(br, attrs[url_index].strip(), attrs[last_update_index].strip(), attrs[submitter_index].strip())

driver.close()
print 'finished all the KB scanning'
