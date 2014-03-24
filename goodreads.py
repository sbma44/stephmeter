import mechanize
import cookielib
import BeautifulSoup
import lxml.html
import json
import re

from settings import *

def login():
    # Browser
    br = mechanize.Browser()

    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)

    # Browser options
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)

    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    # User-Agent (this is cheating, ok?)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    r = br.open(GOODREADS_LOGIN_URL)
    target_form = None
    for (i,f) in enumerate(br.forms()):
        if f.name=='sign_in':
            br.select_form(nr=i)

    br.form['user[email]'] = GOODREADS_LOGIN
    br.form['user[password]'] = GOODREADS_PASSWORD
    br.submit()

    return br


def fetch_stats(br, url):
    br.open(url)
    html = br.response().read()

    root = lxml.html.document_fromstring(html)
    re_value = re.compile(r'(?P<varname>\w+)\s*=\s*(?P<expression>\{.*?\})\s*;', re.S)
    stats = {}
    for script_tag in root.cssselect('script'):
        tc = script_tag.text_content()
        if ('year_stats') in tc and ('page_stats' in tc):
            matches = re_value.findall(tc)
            if matches is not None:
                for m in matches:     
                    stats[m[0]] = json.loads(m[1])

    return stats

def main():
    br = login()
    stats = fetch_stats(br, GOODREADS_TOM_URL)
    print stats

if __name__ == '__main__':
    main()