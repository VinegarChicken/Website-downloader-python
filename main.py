from contextlib import redirect_stderr
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

"""
Returns a tuple. The first element is a request object if succesful, and an error message if the request fails.
The second element is a boolean for whether or not the returned tuple is an error.
"""
def getReq(url, headers=headers):
    """
    Error handling (TODO: Catch more errors)
    """
    try:
        request = req.get(url, headers=headers)
    except MissingSchema: 
        return ("Invalid Url. Are you missing http:// or https:// ?", True)
    except ConnectionError:
        return ("Failed to establish connection with server: {}".format(url), True)
    except InvalidSchema:
        return ("Invalid Schema: {} Is this http or https ?".format(url) , True)
    status = request.status_code
    """
    If the status code is >= 400 than it's an error. Else it's successful
    """
    if status >= 400:
        return (responses[status] + " [{}]".format(status), True)
    return (request, False)
    
    
"""
Recursively get links from website (I only used recursion because I was in a rush. Probably the worst way to do this. Gonna redo without recursion)
This doesn't fetch all the links from a website yet. Most of them. There are also some repeat links (again this was rushed)
"""
def getAllLinksRecursive(link, depth, urlList=[], currentIndex = 0):
    """
    If the link isn't valid, get the next url
    """
    if not link.__contains__("http://") and not link.__contains__("https://"):
        currentIndex +=1
        getAllLinksRecursive(urlList[currentIndex], depth, urlList, currentIndex)
    request = getReq(link)

    """
    Lines 75-79
    If the request is an error and the urllist is empty return an empty List
    If the current url is an error but it isn't the last url in the List go to the next one  
    """
    if request[1] and urlList == []:
        return []
    elif request[1] and currentIndex < len(urlList):
        currentIndex +=1
        getAllLinksRecursive(urlList[currentIndex], depth, urlList, currentIndex)
    else:
        """
        The depth is the amount of urls the crawler should recursively search.
        html file -> html file refrenced inside html file -> html file refrenced inside previously refrenced html file, etc. Doesn't fully work as intended yet
        TODO: Check for links on other types of files that aren't just html
        """
        depth -=1
        if depth == 0:
            return urlList
        """
        Lines 93-119
        BeautifulSoup is an html parsing library. Creates an instance
        Increments through each html tag found (below is what each round in the loop)
        Check if the tag is None (null) or not. In python even if the type of variable isn't acually a boolean, it's false if it's None and true if its not None.
        Check for attributes in tags. Usually in html if a tag has 'src' or 'href' it has a link to a file
        Check if the file is not a http/https link since theres no need to download it. When the use run's the downloaded site, html will send a get request for the file.
        The code looks for things like <script src="file.js"></script> or <link href="styles/style.css"> NOT <script src="https://some.site.link/file.js"></script>
        Join the base url with the file path on the server. Eg if the base site link is https://some.site.link, and the js file path on the server is /jsfiles/file.js"
        The joined url is "https://some.site.link/jsfiles/file.js"
        Add the above url to the urlList
        Repeat
        """
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
        "After the loop completes Incement the current url number"
        currentIndex += 1
        if len(urlList) > currentIndex: #If it's not the end of the list repeat and search for more
            getAllLinksRecursive(urlList[currentIndex], depth, urlList, currentIndex)
        #at this point, everything's finished, so return the list
    return urlList
    
    


def main():
    """
    Lines 143-148 command line setup
    """
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
    
    baseurl = args.url #Url to download
    basedir = args.output_directory #Output directory to write all files to
    #Enable file logging
    if args.log_file:
        handle = logging.FileHandler(args.log_file)
        formatter = logging.Formatter("%(asctime)s %(message)s")
        handle.setFormatter(formatter)
        logger.addHandler(handle)
    
    if baseurl and basedir: #Null checks
        urls = getAllLinksRecursive(baseurl, 5)

        os.makedirs(basedir, exist_ok=True)
        
        pb = ProgressBar(max_value=len(urls))

        for url in pb(urls): #Pb is for the progress bar
            logger.info(url) #Log Url to console
            request = getReq(url)
            if request[1]: #An error occurred so log a warning and skip to the next url
                logger.warning(request[0])
                continue
            path = Path(str(urlparse(url).path).strip("/"))
            pathstr = str(path)
            dir = os.path.dirname(path)
            ext = Path(path).suffix

            if pathstr == '.': #If theres no actual path name, then it's likely the index.html.
                pathstr = "index.html"
            elif ext == '':                                                                                   
                """
                Often times theres no .html extension in site. like https://test.com/idk/idk
                Assume it's html (I'll add more checks in the future that it's actual html)
                """        
                ext = ".html"
                pathstr = pathstr + ext 
            os.makedirs(os.path.join(basedir, dir), exist_ok=True)
            if os.path.basename(os.path.join(basedir, pathstr)) != "":
                with open(os.path.join(basedir, pathstr), "wb+") as f:
                    f.write(request[0].content)
                    """
                    Write the request content to file. The only reason I used binary as my output mode is because a use might download a binary file 
                    (That's not the point of this application, but in the future I'm adding more features like this)
                    """
            pb.update() #Update progress bar
    elif args.list_urls and baseurl: #The argument is to list the urls
        urls = getAllLinksRecursive(baseurl, 5)
        for url in urls:
            logger.info(url) #log urls to console
    


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard Interrupt")
