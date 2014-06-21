###
# Copyright (c) 2014, sdmac
# All rights reserved.
###

import supybot.conf as conf
import supybot.registry as registry

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Dict', True)


Dict = conf.registerPlugin('Dict')
conf.registerGlobalValue(Dict, 'apiKey',
    registry.String('foobar', """The Merriam-Webster Dictionary API Key."""))
conf.registerGlobalValue(Dict, 'wordListFile',
    registry.String('words.txt', """The file containing a list of words."""))
