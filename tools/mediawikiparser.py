#!/usr/bin/python

# Process Wikipedia dump files
#
# Jeremy Mortis (mortis@ucalgary.ca)

import os
import sys
import re

import xml.sax
import xml.sax.handler

from article import Article
from article import Tag
import pyuca

class MediaWikiParser(xml.sax.handler.ContentHandler):

    def __init__(self, collator, metadata, consumer):
        self.databucket = ""
        self.collator = collator
        self.metadata = metadata
        self.consumer = consumer
        self.tagstack = []

    def startElement(self, tag, attrs):

        self.tagstack.append([tag, ""])


    def endElement(self, tag):
        entry = self.tagstack.pop()
        
        if entry[0] != tag:
            sys.stderr.write("mismatched tag: " + tag + " " + repr(entry) + "\n")
            return

        if tag == "sitename":
            self.metadata["title"] = self.clean(entry[1], oneline=True)

        elif tag == "base":
            m = re.compile(r"http://(.*?)\.wikipedia").match(entry[1])
            if m:
                self.metadata["index_language"] = m.group(1)
                self.metadata["article_language"] = m.group(1)
        
        elif tag == "title":
            self.title = self.clean(entry[1], oneline=True)
        
        elif tag == "text":
            self.text = self.clean(entry[1])
                        
        elif tag == "page":
            
            if self.weakRedirect(self.title, self.text):
                return
            
            self.text = self.translateWikiMarkupToHTML(self.text)

            self.consumer(self.title, self.text)
            return
            
    def characters(self, data):

        entry = self.tagstack.pop()
        entry[1] = entry[1] + data
        self.tagstack.append(entry)


    def clean(self, s, oneline = False):
        s = s.encode("utf-8")
        s = re.compile(r"^\s*", re.MULTILINE).sub("", s)
        s = re.compile(r"\s*$", re.MULTILINE).sub("", s)
        s = re.compile(r"\n\n*").sub(r"\n",s)
        if oneline:
            s = s.replace("\n", "")
        return s
    
    def weakRedirect(self, title, text):
        p = re.compile(r"#REDIRECT", re.IGNORECASE)
        if p.search(text):
            p = re.compile(r"\[\[(.*?)\]\]")
            m = p.search(text)
            if m:
                redirect = m.group(1)
                redirectKey = self.collator.getCollationKey(redirect)
                titleKey = self.collator.getCollationKey(title)
                if redirectKey == titleKey:
                    #sys.stderr.write("Weak redirect: " + repr(title) + " " + repr(redirect) + "\n")
                    return True
        return False

    def translateWikiMarkupToHTML(self, text):
        
        text = re.compile(r"\n", re.DOTALL).sub("<br>", text)
        text = re.compile(r"\r").sub("", text)
        text = re.compile(r"^#REDIRECT", re.IGNORECASE).sub("See:", text)
        text = re.compile(r"===(.{,80}?)===").sub(r"<h2>\1</h2>", text)
        text = re.compile(r"==(.{,80}?)==").sub(r"<h1>\1</h1>", text)
        text = re.compile(r"'''''(.{,80}?)'''''").sub(r"<b><i>\1</i></b>", text)
        text = re.compile(r"'''(.{,80}?)'''").sub(r"<b>\1</b>", text)
        text = re.compile(r"''(.{,80}?)''").sub(r"<i>\1</i>", text)
        text = re.compile(r"\{\{.{,80}?\}\}").sub(r"", text)
        text = parseLinks(text)
        return text

def parseLinks(s):
    
    while 1:
        left = s.find("[[")
        if left < 0:
            break
        nest = 2
        right = left + 2
        while (nest > 0) and (right < len(s)):
            if s[right] == "[":
                nest = nest + 1
            elif s[right] == "]":
                nest = nest - 1
            right = right + 1
                        
        if (nest != 0):
            print "Mismatched brackets:", str(left), str(right), str(nest)
            return
                        
        link = s[left:right]
        #print "Link:", link.encode("utf-8")
            
        # recursively parse nested links
        link = parseLinks(link[2:-2])

        p = link.split("|")

        c = p[0].find(":")

        if c >= 0:
            t = p[0][:c]
        else:
            t = ""

        if t == "Image":
            r = '<img href="' + p[0][c+1:] + '">' + p[-1] + '</img>'
        elif t == "Category":
            r = ""
        elif len(t) == 2:
            # link to other language wikipedia
            r = ""
        else:
            r = '<a href="' + p[0] + '">' + p[-1] + '</a>'

        s = s[:left] + r + s[right:] 
        
    return s


def articlePrinter(title, article):
    print "=================================="
    print title
    print "=================================="
    print article

    
if __name__ == '__main__':

    collator = pyuca.Collator("allkeys.txt", strength = 1)    

    string = "<mediawiki><siteinfo><sitename>Wikipedia</sitename><base>http://fr.wikipedia.org/boogy</base></siteinfo><page><title>hiho</title><text>''blah'' [[Image:thing.png|right|See [[thing article|thing text]]]] cows {{go}} bong</text></page></mediawiki>"

    print string
    print ""

    metadata = {}
    
    xml.sax.parseString(string, MediaWikiParser(collator, metadata, articlePrinter))

    print metadata
    print "Done."

