from genericpath import exists
import requests as req, sys, os
from bs4 import BeautifulSoup as BS
from urllib.parse import *
from urllib import parse
from pathlib import *
from requests.exceptions import *
from random import randint
from time import sleep
import logging
import progressbar
from progressbar import ProgressBar
import sys
import argparse
from http.client import responses
import cssutils

cssutils.log.setLevel(logging.CRITICAL)

progressbar.streams.wrap_stderr()
logging.basicConfig()
logger = logging.getLogger('main')
logger.setLevel(logging.INFO)



headers = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
}

def getReq(url, headers=headers):
    try:
        request = req.get(url, headers=headers)
    except MissingSchema:
        return ("Invalid Url. Are you missing http:// or https:// ?", True)
    except ConnectionError:
        return ("Failed to establish connection with server: {}".format(url), True)
    except InvalidSchema:
        return ("Invalid Schema: {} Is this http or https ?".format(url) , True)
    status = request.status_code
    if status >= 400:
        return (responses[status] + " [" + str(status) + "]", True)
    return (request, False)
    
    

def getAllLinksRecursive(link, depth, urlList=[], currentIndex = 0):
    if not link.__contains__("http://") and not link.__contains__("https://") and urlList != []:
        currentIndex +=1
        getAllLinksRecursive(urlList[currentIndex], depth, urlList, currentIndex)
    request = getReq(link)

    if request[1]:
        return urlList
    else:
        depth -=1
        if depth == 0:
            return urlList

        b = BS(request[0].text, 'lxml')
        for tags in b.recursiveChildGenerator():
            if tags.name:
                if tags.get('src'):
                    file = tags.get('src')
                    if not file.__contains__("http://") and not file.__contains__("https://"):
                        newurl = parse.urljoin(link, file)
                        urlList.append(newurl)                        
                if tags.get('href'):
                    file = tags.get('href')
                    """
                    This was to download more css files. Atm some are missing. Will be fixed soon.
                    if file.__contains__(".css"):
                        newcssurl = parse.urljoin(link, file)
                        cssparse = cssutils.parseUrl(newcssurl)
                        cssList = [newcssurl]
                        cssIndex = 0
                        while cssIndex < len(cssList) and cssList != [newcssurl]:
                            for i in cssList[cssIndex].cssRules.rulesOfType(cssutils.css.CSSRule.IMPORT_RULE):
                                cssIndex +=1
                                cssimporturl = parse.urljoin(link, "{}/{}".format(os.path.dirname(newcssurl), i.href))
                                cssList.append(cssimporturl)
                        urlList = urlList + cssList
                    """
                    if not file.__contains__("http://") and not file.__contains__("https://"):
                        newurl = parse.urljoin(link, file)
                        urlList.append(newurl)
        currentIndex += 1
        if len(urlList) > currentIndex:
            getAllLinksRecursive(urlList[currentIndex], depth, urlList, currentIndex)
    return urlList
    
    


def main():
    parser = argparse.ArgumentParser(description="Download Web Sites")
    parser.add_argument('--url', help='Url to download', metavar="<url>", required=True)
   # parser.add_argument('--console-log', help='log to console. ', default=True)
    parser.add_argument('-outdir', '--output-directory', help='Directory to download files', metavar='<Directory Path>', required=False)
    parser.add_argument('-logf', '--log-file', help='Create a log file', metavar='<File Path>', required=False)
    parser.add_argument('-l', '--list-urls', action='store_true', help='List all found urls', required=False)
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()
    else:
        args = parser.parse_args()
    
    baseurl = args.url
    basedir = args.output_directory

    if args.log_file:
        handle = logging.FileHandler(args.log_file)
        formatter = logging.Formatter("%(asctime)s %(message)s")
        handle.setFormatter(formatter)
        logger.addHandler(handle)
    
    if baseurl and basedir:
        urls = getAllLinksRecursive(baseurl, 5)

        os.makedirs(basedir, exist_ok=True)
        
        pb = ProgressBar(max_value=len(urls))

        for url in pb(urls):
            logger.info(url)
            request = getReq(url)
            if request[1]:
                logger.warning(request[0])
                continue
            path = Path(str(urlparse(url).path).strip("/"))
            pathstr = str(path)
            dir = os.path.dirname(path)
            ext = Path(path).suffix

            if pathstr == '.':
                pathstr = "index.html"
            elif ext == '':
                ext = ".html"
                pathstr = pathstr + ext
            os.makedirs(os.path.join(basedir, dir), exist_ok=True)
            if os.path.basename(os.path.join(basedir, pathstr)) != "":
                with open(os.path.join(basedir, pathstr), "wb+") as f:
                    f.write(request[0].content)
            pb.update()
    elif args.list_urls and baseurl:
        urls = getAllLinksRecursive(baseurl, 5)
        for url in urls:
            logger.info(url)
    


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
