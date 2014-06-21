###
# Copyright (c) 2014, sdmac
# All rights reserved.
###

import random
import requests
from xml.dom import minidom

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks


def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


class Entry(object):
    def __init__(self, id):
        self.id = id
        self.funcLabel = None
        self.defTexts = []

    def parse(self, tree):
        self.funcLabel = getText(tree.getElementsByTagName("fl")[0].childNodes)
        for d in tree.getElementsByTagName("def")[0].childNodes:
            if d.nodeType == d.ELEMENT_NODE:
                if d.nodeName == 'sn':
                    num = getText(d.childNodes)
                    if ' ' in num:
                        num = num.replace(' ', '. ')
                if d.nodeName == 'sd':
                    sd = getText(d.childNodes)
                    if len(sd):
                        sd = "; %s" % sd
                if d.nodeName == 'dt':
                    txt = self.getDefText(d.childNodes)
                if len(txt):
                    line = txt
                    if len(sd):
                        line = "; %s %s" % (sd, line)
                    if len(num):
                        line = "%s. %s" % (num, line)
                    defns.append(line)
                    (num, txt, sd) = ('', '', '')
            defs.append((fl, defns))


class Dict(callbacks.Plugin):
    """I can haz word definitions."""
    baseUrl = 'http://www.dictionaryapi.com/api/v1/references'

    def __init__(self, irc):
        self.__parent = super(Dict, self)
        self.__parent.__init__(irc)
        self.wordListFile = self.registryValue('wordListFile')
        self.words = [line.strip() for line in open(self.wordListFile)]

    def listCommands(self):
        return self.__parent.listCommands(["define"])

    def _getDefText(self, nodelist):
        rc = []
        for node in nodelist:
            self.log.debug(' Child node: %s, %s, %s %s'
                           % (node.nodeType,
                              node.nodeName,
                              node.nodeValue,
                              node.attributes))
            if node.nodeType == node.TEXT_NODE:
                self.log.debug('  Text node: %s' % node.data)
                text = node.data.strip(':')
                if len(text):
                    rc.append(text)
            if node.nodeType == node.ELEMENT_NODE:
                if node.nodeName == 'd_link':
                    rc.append(getText(node.childNodes))
                if node.nodeName == 'sx':
                    sx = getText(node.childNodes)
                    if len(rc):
                        sx = "; %s" % sx
                    rc.append(sx)
        return ''.join(rc).strip(' ')

    def _define(self, word, maxNum=3):
        defs = []
        payload = {'key': self.registryValue('apiKey')}
        r = requests.get("%s/collegiate/xml/%s" % (self.baseUrl, word),
                         params=payload)
        tree = minidom.parseString(r.content)
        for n, e in enumerate(tree.getElementsByTagName("entry"), start=1):
            if n > maxNum:
                break;
            defns = []
            (num, txt, sd) = ('', '', '')
            fl = getText(e.getElementsByTagName("fl")[0].childNodes)
            for d in e.getElementsByTagName("def")[0].childNodes:
                if d.nodeType == d.ELEMENT_NODE:
                    if d.nodeName == 'sn':
                        num = getText(d.childNodes)
                        if ' ' in num:
                            num = num.replace(' ', '. ')
                    if d.nodeName == 'sd':
                        sd = getText(d.childNodes)
                        if len(sd):
                            sd = "; %s" % sd
                    if d.nodeName == 'dt':
                        txt = self._getDefText(d.childNodes)
                    if len(txt):
                        line = txt
                        if len(sd):
                            line = "; %s %s" % (sd, line)
                        if len(num):
                            line = "%s. %s" % (num, line)
                        defns.append(line)
                        (num, txt, sd) = ('', '', '')
            defs.append((fl, defns))
        return defs

    def define(self, irc, msg, args, word):
        definitions = self._define(word)
        if definitions:
            out = []
            for (fl, defns) in definitions:
                out.append("[%s]" % fl)
                for d in defns:
                    out.append(" %s" % d)
            irc.replies(out, prefixNick=False)
        else:
            irc.reply('nothin\' there')
    define = wrap(define, ['text'])

    def random(self, irc, msg, args):
        word = random.choice(self.words)
        definitions = self._define(word)
        if definitions:
            out = []
            out.append(word)
            for (fl, defns) in definitions:
                out.append("[%s]" % fl)
                for d in defns:
                    out.append(" %s" % d)
            irc.replies(out, prefixNick=False)
        else:
            irc.reply('nothin\' there')
    random = wrap(random)

    def dictionary(self, irc, msg, args):
        self.random(irc, msg, args)
    dictionary = wrap(dictionary)


Class = Dict

