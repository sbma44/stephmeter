import mechanize
import cookielib
import BeautifulSoup
import lxml.html
import json
import re

from settings import *

class GoodReadsInterface(object):
    """Collects reader stats from friends on Goodreads"""
    def __init__(self):
        super(GoodReadsInterface, self).__init__()
        self.login() 

    def login(self):
        # Browser
        self.br = mechanize.Browser()

        # Cookie Jar
        self.cj = cookielib.LWPCookieJar()
        self.br.set_cookiejar(self.cj)

        # Browser options
        self.br.set_handle_equiv(True)
        self.br.set_handle_gzip(True)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_robots(False)

        # Follows refresh 0 but not hangs on refresh > 0
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

        # User-Agent (this is cheating, ok?)
        self.br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

        r = self.br.open(GOODREADS_LOGIN_URL)
        target_form = None
        for (i,f) in enumerate(self.br.forms()):
            if f.name=='sign_in':
                self.br.select_form(nr=i)

        self.br.form['user[email]'] = GOODREADS_LOGIN
        self.br.form['user[password]'] = GOODREADS_PASSWORD
        self.br.submit()


    def fetch_stats(self, url):
        self.br.open(url)
        html = self.br.response().read()

        # handle login timeout
        if 'You are being <a href="https://www.goodreads.com/user/new?remember=true">redirected</a>.' in html:
            self.login()
            self.br.open(url)
            html = self.br.response().read()

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
    gr = GoodReadsInterface()
    for (name, url) in {'tom': GOODREADS_TOM_URL, 'ben': GOODREADS_BEN_URL, 'kay': GOODREADS_KAY_URL}.items():
        stats = gr.fetch_stats(url)
        print name, stats

if __name__ == '__main__':
    main()