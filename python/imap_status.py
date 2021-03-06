# -*- coding: utf-8 -*-
# Copyright (c) 2009-2015 by xt <xt@bash.no>
# (this script requires WeeChat 0.3.0 or newer)
#
# History:
# 2015-01-09, nils_2
#   version 0.7: use eval_expression()
# 2010-07-12, TenOfTen
#   version 0.6: beautify notification area
# 2010-03-17, xt
#   version 0.5: fix caching of return message
# 2010-01-19, xt
#   version 0.4: only run check when timer expired
# 2009-11-03, xt
#   version 0.3: multiple mailbox support
# 2009-11-02, xt
#   version 0.2: remove the imap "client" buffer, just do the unread count
# 2009-06-18, xt <xt@bash.no>
#   version 0.1: initial release.
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
'''
Usage: put [imap] in your status bar items.  (Or any other bar to your liking)
"/set weechat.bar.status.items".

Warning: If you have a slow imap server, weechat might "freeze" while doing operations against remove server as this script does not do any background processing and weechat is single threaded.
'''

import weechat as w
import imaplib as i
from time import time as now
import re

SCRIPT_NAME    = "imap_status"
SCRIPT_AUTHOR  = "xt <xt@bash.no>"
SCRIPT_VERSION = "0.7"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC    = "Bar item with unread imap messages count"


LAST_RUN = 0
LAST_MESSAGE = ''

# script options
settings = {
    "username"          : '',
    "password"          : '',
    "hostname"          : '', # gmail uses imap.gmail.com
    "port"              : '993',
    'mailboxes'         : 'INBOX', #comma separated list of mailboxes. "Inbox" works fine too with gmail.
    'message'           : 'Mail: ',
    'message_color'     : 'default',
    'count_color'       : 'default',
    'interval'          : '5',
}

class Imap(object):
    ''' Simple helper class for interfacing with IMAP server '''

    iRe = re.compile("UNSEEN (\d+)")
    conn = False

    def __init__(self):
        ''' Connect and login'''
        username = string_eval_expression( w.config_get_plugin('username') )
        password = string_eval_expression( w.config_get_plugin('password') )
        hostname = string_eval_expression( w.config_get_plugin('hostname') )
        port = int(w.config_get_plugin('port'))

        if username and password and hostname and port:
             M = i.IMAP4_SSL(hostname, port)
             M.login(username, password)
             self.conn = M

    def unreadCount(self, mailbox='INBOX'):
        if self.conn:
            unreadCount = int(self.iRe.search(\
                self.conn.status(mailbox, "(UNSEEN)")[1][0]).group(1))
            return unreadCount
        else:
            w.prnt('', 'Problem with IMAP connection. Please check settings.')
            return 0

    def logout(self):
        if not self.conn:
            return
        try:
            self.conn.close()
        except Exception, e:
            self.conn.logout()


def imap_cb(*kwargs):
    ''' Callback for the bar item with unread count '''

    global LAST_RUN, LAST_MESSAGE

    # Check LAST RUN if we need to run again
    if (now() - LAST_RUN) < int(w.config_get_plugin('interval'))*60:
        return LAST_MESSAGE

    imap = Imap()

    if not w.config_get_plugin('message'):
        output = ""
    else:
        output = '%s%s: ' % (\
            w.color(w.config_get_plugin('message_color')),
            w.config_get_plugin('message'))
    any_with_unread = False
    mailboxes = w.config_get_plugin('mailboxes').split(',')
    for mailbox in mailboxes:
        mailbox = mailbox.strip()
        unreadCount = imap.unreadCount(mailbox)
        if unreadCount > 0:
            any_with_unread = True
            output += '%s%s: %s%s ' %(w.color(w.config_get_plugin('message_color')),
                mailbox,
                w.color(w.config_get_plugin('count_color')),
                unreadCount)
    imap.logout()
    if output:
        output = output[:-1]
    output += w.color('reset')

    LAST_RUN = now()
    LAST_MESSAGE = ''

    if any_with_unread:
        LAST_MESSAGE = output

    return LAST_MESSAGE

def imap_update(*kwargs):
    w.bar_item_update('imap')

    return w.WEECHAT_RC_OK

def string_eval_expression(text):
    if int(version) >= 0x00040200:
        return w.string_eval_expression(text,{},{},{})
    return text

if w.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
        SCRIPT_DESC, '', ''):
    for option, default_value in settings.iteritems():
        if not w.config_is_set_plugin(option):
            w.config_set_plugin(option, default_value)

    version = w.info_get("version_number", "") or 0

    w.bar_item_new('imap', 'imap_cb', '')
    w.hook_timer(\
            int(w.config_get_plugin('interval'))*1000*60,
            0,
            0,
            'imap_update',
            '')
