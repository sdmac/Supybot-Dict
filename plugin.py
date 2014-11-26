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


class Meaning(object):
    def __init__(self, senseNumNode=None):
        self.elems = []
        self.senseNum = []
        if senseNumNode:
            self._parseSenseNum(senseNumNode)

    def _parseSenseNum(self, node):
        for child in node.childNodes:
            if child.nodeType == node.TEXT_NODE:
                if child.data:
                    for numPart in child.data.strip().split(' '):
                        self.senseNum.append(numPart)
            elif child.nodeType == node.ELEMENT_NODE:
                if child.nodeName == 'snp':
                    self.senseNum.append(getText(child.childNodes))

    def _getDefText(self, nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                text = node.data.strip(': ')
                if len(text):
                    rc.append(text)
            if node.nodeType == node.ELEMENT_NODE:
                if node.nodeName == 'd_link':
                    rc.append(getText(node.childNodes))
                if node.nodeName == 'sx':
                    sx = getText(node.childNodes)
                    if len(rc):
                        sx = ", %s" % sx
                    rc.append(sx)
        return ''.join(rc).strip(' ')

    def getSenseNumber(self):
        return self.senseNum

    def setSenseNumber(self, node):
        self._parseSenseNum(node)

    def parseDefElement(self, node):
        if node.nodeName == 'dt':
            self.elems.append(('dt', self._getDefText(node.childNodes)))
        elif node.nodeName == 'sd':
            self.elems.append(('sd',  getText(node.childNodes)))

    def valid(self):
        return len(self.elems) > 0

    def __repr__(self):
        rep = ''.join(["{0}. ".format(num) for num in self.senseNum])
        for (type, value) in self.elems:
            if type == 'dt':
                rep = "{0} {1}".format(rep, value)
            elif type == 'sd':
                rep = "{0}; {1}:".format(rep, value)
        return rep


class Entry(object):
    def __init__(self, id):
        self.id = id
        self.funcLabel = None
        self.defTexts = []

    def parse(self, tree):
        meaning = Meaning()
        meanings = []
        self.funcLabel = getText(tree.getElementsByTagName("fl")[0].childNodes)
        for d in tree.getElementsByTagName("def")[0].childNodes:
            if d.nodeType == d.ELEMENT_NODE:
                if d.nodeName == 'sn':
                    if meaning.getSenseNumber():
                        if meaning.valid() is True:
                            meanings.append(meaning)
                        meaning = Meaning(d)
                    else:
                        meaning.setSenseNumber(d)
                elif d.nodeName == 'vt':
                    pass
                else:
                    meaning.parseDefElement(d)

        return (self.funcLabel, [str(m) for m in meanings])


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

    def _define(self, word, maxNum=3):
        defs = []
        payload = {'key': self.registryValue('apiKey')}
        r = requests.get("%s/collegiate/xml/%s" % (self.baseUrl, word),
                         params=payload)
        tree = minidom.parseString(r.content)
        for n, e in enumerate(tree.getElementsByTagName("entry"), start=1):
            if n > maxNum:
                break;
            entry = Entry(e.getAttribute('id'))
            defs.append(entry.parse(e))
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

