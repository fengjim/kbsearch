from selenium import webdriver

driver = webdriver.PhantomJS()
#driver.set_window_size(1120, 550)
driver.implicitly_wait(5)

driver.get('http://kb.vmware.com/kb/2120653')
elements = driver.find_elements_by_class_name('uiOutputDate')

# todo: check login needed, so save the wait time
#eles = driver.find_elements_by_class_name('salesforceIdentityLoginForm2')

#eles = driver.find_elements_by_id('auraAppcacheProgress')
driver.save_screenshot('out.png');

for element in elements:
    print elelemente.text
