
import sys
import os
import sqlite3
from datetime import datetime

from . import kodilogging
from . import kodiutils
from . import settings
from . import encryption

import six
from six.moves import urllib_parse
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs

import re
import requests
# import random
# import string
import web_pdb
import uuid
import math
import logging
from json import dumps, loads
import random
import string
import time
from base64 import b64encode
import urllib

# Python 2 and 3: option 3
try:
    import itertools.imap as map
except ImportError:
    pass
import operator


# import server
import inputstreamhelper
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

params = dict(urllib_parse.parse_qsl(sys.argv[2][1:]))

addon = xbmcaddon.Addon()
_settings = addon.getSetting
logger = logging.getLogger(addon.getAddonInfo('id'))
kodilogging.config()

# Init Encryption
aes = encryption.AESCipher()

# SQLite  Database Name
TRANSLATEPATH = xbmcvfs.translatePath if six.PY3 else xbmc.translatePath

rootDir = addon.getAddonInfo('path')
if rootDir[-1] == ';':
    rootDir = rootDir[0:-1]
rootDir = TRANSLATEPATH(rootDir)
resDir = os.path.join(rootDir, 'resources')
libDir = os.path.join(resDir, 'lib')
profileDir = addon.getAddonInfo('profile')

channeldb = os.path.join(libDir, 'sunnxt.db')

_addonname = addon.getAddonInfo('name')
# _version = addon.getAddonInfo('version')
# _addonID = addon.getAddonInfo('id')
_icon = addon.getAddonInfo('icon')
_fanart = addon.getAddonInfo('fanart')

platform = 'desktop_web'
languages = settings.get_languages()
session = requests.Session()
ITEMS_LIMIT = 10
# device_id= 'o7JvbEPk3KRA14d8FwEr000000000000'
# device_id= '4363debbc0dded755df0b635277271c0'
# device_id= 'iIxsxYf40cqO3koIkwzKHZhnJzHN13zb"
# device_id= 'WebBrowser'
# platform = 'web_app'
# Initialise the token.

deviceid = addon.getSetting('deviceID')
ESK_SECRET_KEY = 'HOBNPuy7H3T5meJJAfyLkJlHaX2dXeEB'
# deviceid = None
if deviceid:
    device_id = deviceid
else:
    # device_id = '77878d98-0aa9-44ff-a5c0-84fd6e39e518'
    device_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20)).ljust(32, '0')
    addon.setSetting(
        "deviceid", device_id)

# window = xbmcgui.Window(10000)
cache = StorageServer.StorageServer('zee5', 4)

"""
headers = {"user-agent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'}

def get_header():
    url='https://www.zee5.com/requestheaders'
    data = requests.get(url,headers=headers).json()
    for name, value in six.iteritems(data):
        headers[name]=value
    return


get_header()
headers["content-type"] = "application/json"

"""
headers = {
    "origin": "https://www.sunnxt.com",
    "referer": "https://www.sunnxt.com/",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "contentlanguage": "tamil,telugu,malayalam,kannada,bengali,marathi",
    "content-type": "application/json",
    "cache-control": "no-cache",
    "connection": "keep-alive",
    "sec-ch-ua-platform": "Linux; Android 7.1.1",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-myplex-maturity-level": "",
    "X-myplex-platform": "browser"
}


try:
    platform = re.findall(r'\(([^)]+)', xbmc.getUserAgent())[0]
except:
    platform = 'Linux; Android 7.1.1'

USER_AGENT = "Mozilla/5.0 ({}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36 Firefox/95.0".format(platform)
# USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/121.0.6167.85 Safari/537.36"
headers["user-agent"] = USER_AGENT


def getCookies(cookie_jar, domain):
    cookie_dict = cookie_jar.get_dict(domain=domain)
    found = ['%s=%s' % (name, value) for (name, value) in cookie_dict.items()]
    return ';'.join(found)

def get_channel_data(channel_id):
    conn = sqlite3.connect(channeldb)
    conn.row_factory = sqlite3.Row
    conn.text_factory = str
    c = conn.cursor()
    record = None

    # web_pdb.set_trace()
    try:
        c.execute("SELECT * FROM channel WHERE channel_id = '{}'".format(channel_id))
        record = c.fetchone()
        conn.close()
        return record
    except:
        conn.close()
        return record

def get_token():
    # url = 'https://useraction.zee5.com/token/platform_tokens.php?platform_name=web_app'
    url = 'https://launchapi.zee5.com/launch?platform_name=web_app'
    data = requests.get(url, headers=headers).json()
    # headers["x-access-token"] = data['platform_token']['token']
    return


def gen_esk() -> bytes:
    """
    Generates the ESK based on the algorithm grabbed from
    ZEETV APK
    """
    esk_string = f'{device_id}__{ESK_SECRET_KEY}__{int(time.time()) * 1000}'

    return b64encode(esk_string.encode())


def add_device():
    url = "https://subscriptionapi.zee5.com/v1/device"
    body = {"name": "WebBrowser", "identifier": device_id}
    body = dumps(body)
    jd = requests.post(url, headers=headers, data=body).json()
    if jd.get('code') == 3602:
        url = "https://subscriptionapi.zee5.com/v1/device"
        jd = requests.delete(url, headers=headers).json()
    elif jd.get('code') == 401:
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)' %
                            (_addonname, jd.get('message'), 3000, _icon))
    return


def loginold():
    email = addon.getSetting('email')
    password = addon.getSetting('password')

    if email:
        Pattern = re.compile("[6-9][0-9]{9}")
        if (Pattern.match(email)):
            url = "https://whapi.zee5.com/v1/user/loginMobile_v2.php"
        else:
            url = "https://whapi.zee5.com/v1/user/loginemail_v2.php"

        if (Pattern.match(addon.getSetting('email'))):
            body = {"aid": "91955485578", "guest_token": "48b30b9e-b677-4669-a079-5edc36bf54f9", "lotame_cookie_id": "", "mobile": "91" + email, "password": password, "platform": "web", "version": "2.50.87"}
        else:
            body = {"aid": "91955485578", "guest_token": "48b30b9e-b677-4669-a079-5edc36bf54f9", "lotame_cookie_id": "", "email": email, "password": password, "platform": "web", "version": "2.50.50"}

        body = dumps(body)

        jd = requests.post(url, headers=headers, data=body).json()

        if jd.get('access_token'):
            headers.update({'Authorization': 'bearer ' + jd['access_token']})
            addon.setSetting(
                "Authorization", 'bearer ' + jd['access_token'])
            add_device()
        else:
            xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (_addonname, "Invalid login credential", 3000, _icon))
    return


def loginold2():
    email = addon.getSetting('email')
    # web_pdb.set_trace()
    if email:
        Pattern = re.compile("[6-9][0-9]{9}")
        if (Pattern.fullmatch(email)):
            url = "https://b2bapi.zee5.com/device/sendotp_v1.php?phoneno=91%s" % email
            jd = requests.get(url, headers=headers).json()
            xbmc.log(dumps(jd))
            if jd.get('code') == 0:
                OTP = xbmcgui.Dialog().numeric(0, "Enter OTP")
                url = "https://b2bapi.zee5.com/device/verifyotp_v1.php?phoneno=91{}&otp={}&guest_token={}&platform=web".format(
                    email,
                    OTP,
                    device_id
                )

        jd = requests.get(url, headers=headers).json()
        xbmc.log(dumps(jd))
        if jd.get('token'):
            headers.update({'Authorization': 'bearer ' + jd['token']})
            addon.setSetting(
                "Authorization", 'bearer ' + jd['token'])
            add_device()
        else:
            xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (
                _addonname, jd.get('message'), 3000, _icon))
    return


def login():
    email = addon.getSetting('email')
    password = addon.getSetting('password')
    hdr = headers
    # hdr.update({'esk': gen_esk()})
    # hdr.update({'device_id': device_id})

    if email:
        url = "https://www.sunnxt.com/next/api/login"
        credentials = {"userid":email,"password":password}

        payload = aes.encrypt(dumps(credentials).replace(' ',''))
        body = {"payload": payload, "version": 1}

        body = urllib.parse.urlencode(body)
        client = requests.Session()

        hdr1 = hdr
        hdr1['Content-Type'] = 'application/x-www-form-urlencoded'
        json_data = client.post(url, headers=hdr1, data=body).json()

        jd = aes.decrypt(json_data.get('response'))

        xbmc.log(dumps(jd), xbmc.LOGINFO)

        jd = loads(jd)
        if jd.get('status') == "SUCCESS":
            client_cookies = getCookies(client.cookies, '.www.sunnxt.com')
            headers.update({'Cookie': client_cookies})
            addon.setSetting(
                "SessionID", client.cookies['sessionid'])
            add_device()
            # xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(_addonname, "login Successful", 3000, _icon))
        else:
            xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (
                _addonname, jd.get('message'), 3000, _icon))
    return


def login_z5():
    email = addon.getSetting('email')
    password = addon.getSetting('password')
    hdr = headers
    # hdr.update({'esk': gen_esk()})
    # hdr.update({'device_id': device_id})

    if email:
        Pattern = re.compile("[6-9][0-9]{9}")
        if (Pattern.match(email)):
            url = "https://auth.zee5.com/v1/user/sendotp"
            body = {"phoneno": "91" + email}
            body = dumps(body)
            jd = requests.post(url, headers=hdr, data=body).json()

            if jd.get('code') == 0:
                OTP = xbmcgui.Dialog().numeric(0, "Enter OTP")
                url = "https://auth.zee5.com/v1/user/verifyotp"
                body = {"phoneno": "91" + email, "platform": "PWA", "otp": OTP, "guest_token": device_id,
                        "appsflyer_id": "65368gdbso90oNinja4AS133436", "lotame_cookie_id": "", "aid": "91955485578", "device": "Desktop", "version": "2.52.59"}
                # web_pdb.set_trace()
        else:
            url = "https://auth.zee5.com/v2/user/loginemail"
            body = {"aid": "91955485578", "guest_token": device_id,
                    "email": email, "password": password, "platform": "PWA", "version": "2.52.59"}

        body = dumps(body)
        jd = requests.post(url, headers=hdr, data=body).json()
        xbmc.log(dumps(jd), xbmc.LOGINFO)

        if jd.get('access_token'):
            headers.update({'Authorization': 'bearer ' + jd['access_token']})
            addon.setSetting(
                "Authorization", 'bearer ' + jd['access_token'])
            add_device()
            # xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(_addonname, "login Successful", 3000, _icon))
        else:
            xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (
                _addonname, jd.get('message'), 3000, _icon))
    return


def loginold():
    email = addon.getSetting('email')
    password = addon.getSetting('password')

    if email:
        Pattern = re.compile("[6-9][0-9]{9}")
        if (Pattern.match(email)):
            url = "https://whapi.zee5.com/v1/user/loginMobile_v2.php"
        else:
            url = "https://whapi.zee5.com/v1/user/loginemail_v2.php"

        if (Pattern.match(addon.getSetting('email'))):
            body = {"aid": "91955485578", "guest_token": "48b30b9e-b677-4669-a079-5edc36bf54f9", "lotame_cookie_id": "", "mobile": "91" + email, "password": password, "platform": "web", "version": "2.50.87"}
        else:
            body = {"aid": "91955485578", "guest_token": "48b30b9e-b677-4669-a079-5edc36bf54f9", "lotame_cookie_id": "", "email": email, "password": password, "platform": "web", "version": "2.50.50"}

        body = dumps(body)

        jd = requests.post(url, headers=headers, data=body).json()

        if jd.get('access_token'):
            headers.update({'Authorization': 'bearer ' + jd['access_token']})
            addon.setSetting(
                "Authorization", 'bearer ' + jd['access_token'])
            add_device()
        else:
            xbmc.executebuiltin('Notification(%s, %s, %d, %s)' % (_addonname, "Invalid login credential", 3000, _icon))
    return

def get_user():

    url = 'https://userapi.zee5.com/v1/user'
    data = requests.get(url, headers=headers).json()
    if not data.get('code'):
        headers.update({'uid': data['id']})
        Pattern = re.compile("[7-9][0-9]{9}")
        if (Pattern.match(addon.getSetting('email'))):
            headers.update({'mobile': data['mobile']})
        else:
            headers.update({'email': data['email']})
        headers.update({'country': data['registration_country']})
    return


get_token()

if _settings("Authorization"):
    headers.update({"Authorization": _settings("Authorization")})
else:
    login()

# auth = "bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYmYiOjE2NjE1NjcyMTcsImV4cCI6MTY5MzEwMzIxNywiaXNzIjoiaHR0cHM6Ly91c2VyYXBpLnplZTUuY29tIiwiYXVkIjpbImh0dHBzOi8vdXNlcmFwaS56ZWU1LmNvbS9yZXNvdXJjZXMiLCJzdWJzY3JpcHRpb25hcGkiLCJ1c2VyYXBpIl0sImNsaWVudF9pZCI6InJlZnJlc2hfdG9rZW5fY2xpZW50Iiwic3ViIjoiZTc3ZTVkNzMtMmM5OC00OTlkLThiYWUtOTI5MDk1ODQyOTFlIiwiYXV0aF90aW1lIjoxNjYxNTY3MjE3LCJpZHAiOiJsb2NhbCIsInVzZXJfaWQiOiJlNzdlNWQ3My0yYzk4LTQ5OWQtOGJhZS05MjkwOTU4NDI5MWUiLCJzeXN0ZW0iOiJaNSIsImFjdGl2YXRpb25fZGF0ZSI6IjIwMjItMDMtMjVUMTQ6NDU6MDUiLCJjcmVhdGVkX2RhdGUiOiIyMDIxLTA4LTIyVDEzOjMzOjQ1IiwicmVnaXN0cmF0aW9uX2NvdW50cnkiOiJJTiIsInVzZXJfZW1haWwiOiJtYW5pc2guYmFkb2xlQGdtYWlsLmNvbSIsInN1YnNjcmlwdGlvbnMiOiJbe1wiaWRcIjpcIjRjMDllMmNmLWU4ZTMtNDYyZi1iNmY1LTJiNjFlMjQwNDJkNVwiLFwidXNlcl9pZFwiOlwiZTc3ZTVkNzMtMmM5OC00OTlkLThiYWUtOTI5MDk1ODQyOTFlXCIsXCJpZGVudGlmaWVyXCI6XCJDUk1cIixcInN1YnNjcmlwdGlvbl9wbGFuXCI6e1wiaWRcIjpcIjAtMTEtMjA3MFwiLFwiYXNzZXRfdHlwZVwiOjExLFwic3Vic2NyaXB0aW9uX3BsYW5fdHlwZVwiOlwiU1ZPRFwiLFwidGl0bGVcIjpcIlByZW1pdW1cIixcIm9yaWdpbmFsX3RpdGxlXCI6XCJQcmVtaXVtXCIsXCJzeXN0ZW1cIjpcIlo1XCIsXCJkZXNjcmlwdGlvblwiOlwiNDAlIG9mZiBvbiA5OTlcIixcImJpbGxpbmdfY3ljbGVfdHlwZVwiOlwiZGF5c1wiLFwiYmlsbGluZ19mcmVxdWVuY3lcIjozNjUsXCJwcmljZVwiOjU5OS4wLFwiY3VycmVuY3lcIjpcIklOUlwiLFwiY291bnRyeVwiOlwiSU5cIixcImNvdW50cmllc1wiOltcIklOXCJdLFwic3RhcnRcIjpcIjIwMjItMDMtMTRUMDA6MDA6MDBaXCIsXCJlbmRcIjpcIjIwMjItMDctMTRUMDA6MDA6MDBaXCIsXCJvbmx5X2F2YWlsYWJsZV93aXRoX3Byb21vdGlvblwiOnRydWUsXCJyZWN1cnJpbmdcIjpmYWxzZSxcInBheW1lbnRfcHJvdmlkZXJzXCI6W3tcIm5hbWVcIjpcIkp1c1BheVwifSx7XCJuYW1lXCI6XCJBbWF6b25JQVBcIixcInByb2R1Y3RfcmVmZXJlbmNlXCI6XCJ6ZWU1X3ByZW1pdW1fcGFja19pbl8xMm1cIn0se1wibmFtZVwiOlwiUGF5VVwifSx7XCJuYW1lXCI6XCJQYXlUTVwifSx7XCJuYW1lXCI6XCJQYXl0bVFSXCJ9LHtcIm5hbWVcIjpcIlBheXRtUVJVUElcIn0se1wibmFtZVwiOlwiQmlsbGRlc2tcIn0se1wibmFtZVwiOlwiUXdpa2NpbHZlclwifV0sXCJwcm9tb3Rpb25zXCI6W10sXCJhc3NldF90eXBlc1wiOlswLDYsOV0sXCJhc3NldF9pZHNcIjpbXCJcIl0sXCJidXNpbmVzc190eXBlXCI6XCJmcmVlXCIsXCJiaWxsaW5nX3R5cGVcIjpcInByZW1pdW1cIixcIm51bWJlcl9vZl9zdXBwb3J0ZWRfZGV2aWNlc1wiOjMsXCJtb3ZpZV9hdWRpb19sYW5ndWFnZXNcIjpbXSxcInR2X3Nob3dfYXVkaW9fbGFuZ3VhZ2VzXCI6W10sXCJjaGFubmVsX2F1ZGlvX2xhbmd1YWdlc1wiOltdLFwiZHVyYXRpb25fdGV4dFwiOlwiOTk5XCIsXCJ2YWxpZF9mb3JfYWxsX2NvdW50cmllc1wiOnRydWUsXCJhbGxvd2VkX3BsYXliYWNrX2R1cmF0aW9uXCI6NixcIm9mZmVyX2lkXCI6MCxcImNhdGVnb3J5XCI6XCJcIn0sXCJzdWJzY3JpcHRpb25fc3RhcnRcIjpcIjIwMjItMDMtMjZUMDM6MjI6NTAuNjI3WlwiLFwic3Vic2NyaXB0aW9uX2VuZFwiOlwiMjAyMy0wMy0yNlQyMzo1OTo1OVpcIixcInN0YXRlXCI6XCJhY3RpdmF0ZWRcIixcInJlY3VycmluZ19lbmFibGVkXCI6ZmFsc2UsXCJwYXltZW50X3Byb3ZpZGVyXCI6XCJjcm1cIixcImZyZWVfdHJpYWxcIjpudWxsLFwiY3JlYXRlX2RhdGVcIjpcIjIwMjItMDMtMjZUMDM6MjI6NTAuNjI3WlwiLFwiaXBfYWRkcmVzc1wiOlwiMTAzLjE5NS4yNDkuMTg3XCIsXCJjb3VudHJ5XCI6XCJJTlwiLFwicmVnaW9uXCI6XCJNYWhhcmFzaHRyYVwiLFwiYWRkaXRpb25hbFwiOntcImFtb3VudFwiOjUzOSxcInBheW1lbnRfdHhuX2lkXCI6XCJ6ZWU1LTc1MjgwNzAyX1d6S2diQnZld0xBVWh0eDAtMVwiLFwicmVxdWVzdF9jYWxsX2Zyb21cIjpcIkNhbGxiYWNrXCIsXCJwYXltZW50bW9kZVwiOlwiQ3JlZGl0Q2FyZFwiLFwidHJhbnNhY3Rpb25faWRcIjpcIjc1MjgwNzAyX1d6S2diQnZld0xBVWh0eDBcIixcImRpc2NvdW50X2Ftb3VudFwiOlwiMC4wMDAwXCIsXCJmcmVlX3RyaWFsXCI6bnVsbCxcInJlY3VycmluZ19lbmFibGVkXCI6dHJ1ZSxcIm9yaWdpbmFsX3VzZXJfYWdlbnRcIjpcIm9raHR0cC80LjkuMVwiLFwic3Vic2NyaXB0aW9uX3R5cGVcIjpcIlNVQlNDUklQVElPTlwifSxcImFsbG93ZWRfYmlsbGluZ19jeWNsZXNcIjowLFwidXNlZF9iaWxsaW5nX2N5Y2xlc1wiOjB9XSIsInNjb3BlIjpbInN1YnNjcmlwdGlvbmFwaSIsInVzZXJhcGkiLCJvZmZsaW5lX2FjY2VzcyJdLCJhbXIiOlsiZGVsZWdhdGlvbiJdfQ.RuPqBG4BuGt8gbtsiMi3uds2iQ2cc4ct2_bR_YEJn4bp_jcGUTxOTFS6_1Ucq0Gkl6W_6WKyzbiTuQlP4QZgT5WIX3ZY3LZ_HmKMfZUuyk2zQ5W7ZHmYzC9qGIdDCTLhUWbZVP88Y9F631b-BA_fxxgU3WPv_YP9kK-ewbLrt7fDacJTVS17_nxBcBQvCCcFdpvJYwX8wLBETn6D6QL1ZlDMM8GTiIFd5nDJaSKCTe5n-XDgJYs7YYoczpHNn9CuB9uNx9tsJjas9fiZMU65uDEKO2V6ZmAO06ntiQ77I87nrn7JC7VOA_pheXRKrgH-acOC7n6vXBZx6tEDh7qyBw"
# auth = "bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImU2bF9sZjB4enBhWThXME1wVDNaUHM3aHI4RnhjS2tsOENXQlp6RUpPaUEifQ.eyJ1c2VyX2lkIjoiYTI0YjY5OGQtZWQxYy00ZWNhLWE2OWQtOWY3MDYxMTZjZTkxIiwic3lzdGVtIjoiWjUiLCJjdXJyZW50X2NvdW50cnkiOiJVUyIsInJlZ2lzdHJhdGlvbl9jb3VudHJ5IjoiVVMiLCJhY3RpdmF0aW9uX2RhdGUiOiIyMDE5LTA0LTExVDA5OjU3OjMwLjgxN1oiLCJhY3RpdmF0ZWQiOnRydWUsImNyZWF0ZWRfZGF0ZSI6IjIwMTktMDQtMTFUMDk6NTY6MzMuMTIwWiIsInN1YiI6IkEyNEI2OThELUVEMUMtNEVDQS1BNjlELTlGNzA2MTE2Q0U5MSIsImRldmljZV9pZCI6IiIsImlkcCI6ImxvY2FsIiwiY2xpZW50X2lkIjoicmVmcmVzaF90b2tlbiIsImF1ZCI6WyJ1c2VyYXBpIiwic3Vic2NyaXB0aW9uYXBpIiwicHJvZmlsZWFwaSJdLCJzY29wZSI6WyJ1c2VyYXBpIiwic3Vic2NyaXB0aW9uYXBpIiwicHJvZmlsZWFwaSJdLCJhbXIiOlsiZGVsZWdhdGlvbiJdLCJzdWJzY3JpcHRpb25zIjoiW3tcImlkXCI6XCIzNjA4YjIwZC1iZmJlLTQ3ZTEtOTJjYy04MzczMTM4MmNkYTRcIixcInVzZXJfaWRcIjpcImEyNGI2OThkLWVkMWMtNGVjYS1hNjlkLTlmNzA2MTE2Y2U5MVwiLFwiaWRlbnRpZmllclwiOlwiQ1JNXCIsXCJzdWJzY3JpcHRpb25fcGxhblwiOntcImlkXCI6XCIwLTExLTEwODhcIixcImFzc2V0X3R5cGVcIjoxMSxcInN1YnNjcmlwdGlvbl9wbGFuX3R5cGVcIjpcIlNWT0RcIixcInRpdGxlXCI6XCJKaW8gQ29tcGxlbWVudGFyeSBQYWNrXCIsXCJvcmlnaW5hbF90aXRsZVwiOlwiSmlvIENvbXBsZW1lbnRhcnkgUGFja1wiLFwic3lzdGVtXCI6XCJaNVwiLFwiZGVzY3JpcHRpb25cIjpcIkppbyBDb21wbGVtZW50YXJ5IFBhY2tcIixcImJpbGxpbmdfY3ljbGVfdHlwZVwiOlwiZGF5c1wiLFwiYmlsbGluZ19mcmVxdWVuY3lcIjozMCxcInByaWNlXCI6MCxcImN1cnJlbmN5XCI6XCJJTlJcIixcImNvdW50cnlcIjpcIklOXCIsXCJjb3VudHJpZXNcIjpbXCJJTlwiXSxcInN0YXJ0XCI6XCIyMDE5LTA4LTI4VDAwOjAwOjAwWlwiLFwiZW5kXCI6XCIyMDI0LTA2LTMwVDIzOjU5OjU5WlwiLFwib25seV9hdmFpbGFibGVfd2l0aF9wcm9tb3Rpb25cIjpmYWxzZSxcInJlY3VycmluZ1wiOmZhbHNlLFwicGF5bWVudF9wcm92aWRlcnNcIjpbe1wibmFtZVwiOlwiWkVFNVwiLFwicHJvZHVjdF9yZWZlcmVuY2VcIjpudWxsfV0sXCJwcm9tb3Rpb25zXCI6W10sXCJhc3NldF90eXBlc1wiOls2LDAsOV0sXCJhc3NldF9pZHNcIjpbXSxcImZyZWVfdHJpYWxcIjpudWxsLFwiYnVzaW5lc3NfdHlwZVwiOlwiZnJlZVwiLFwiYmlsbGluZ190eXBlXCI6bnVsbCxcIm51bWJlcl9vZl9zdXBwb3J0ZWRfZGV2aWNlc1wiOjUsXCJ0aWVyXCI6bnVsbCxcIm1vdmllX2F1ZGlvX2xhbmd1YWdlc1wiOltdLFwidHZfc2hvd19hdWRpb19sYW5ndWFnZXNcIjpbXSxcImNoYW5uZWxfYXVkaW9fbGFuZ3VhZ2VzXCI6W10sXCJkdXJhdGlvbl90ZXh0XCI6bnVsbCxcInRlcm1zX2FuZF9jb25kaXRpb25zXCI6bnVsbCxcInZhbGlkX2Zvcl9hbGxfY291bnRyaWVzXCI6dHJ1ZSxcImFsbG93ZWRfcGxheWJhY2tfZHVyYXRpb25cIjowLFwib2ZmZXJfaWRcIjpudWxsLFwiY2F0ZWdvcnlcIjpudWxsLFwiYWN0dWFsX3ZhbHVlXCI6bnVsbH0sXCJzdWJzY3JpcHRpb25fc3RhcnRcIjpcIjIwMjItMTAtMTFUMTM6NDM6MzQuNTk3WlwiLFwic3Vic2NyaXB0aW9uX2VuZFwiOlwiMjAyMi0xMi0xMFQyMzo1OTo1OVpcIixcInN0YXRlXCI6XCJhY3RpdmF0ZWRcIixcInJlY3VycmluZ19lbmFibGVkXCI6ZmFsc2UsXCJwYXltZW50X3Byb3ZpZGVyXCI6XCJjcm1cIixcImZyZWVfdHJpYWxcIjpudWxsLFwiY3JlYXRlX2RhdGVcIjpcIjIwMjItMTAtMTFUMTM6NDM6MzQuNTk3WlwiLFwiaXBfYWRkcmVzc1wiOlwiNjUuMS4zOC4xNzNcIixcImNvdW50cnlcIjpudWxsLFwiYWRkaXRpb25hbFwiOntcInBheW1lbnRtb2RlXCI6XCJcIixcInJlY3VycmluZ19lbmFibGVkXCI6XCJ0cnVlXCIsXCJwYXJ0bmVyXCI6XCJqaW9zdGJcIn0sXCJhbGxvd2VkX2JpbGxpbmdfY3ljbGVzXCI6MCxcInVzZWRfYmlsbGluZ19jeWNsZXNcIjowfV0iLCJhY2Nlc3NfdG9rZW5fdHlwZSI6IkhpZ2hQcml2aWxlZ2UiLCJ2ZXJzaW9uIjoxLCJ1c2VyX3R5cGUiOiJSZWdpc3RlcmVkIiwidXNlcl9tb2JpbGUiOiI5MTk4ODQzMzk2NzciLCJhdXRoX3RpbWUiOjE2Njk4MDY4OTIsImV4cCI6MTY4NTU3NDg5MiwiaWF0IjoxNjY5ODA2ODkyLCJpc3MiOiJodHRwczovL3VzZXJhcGkuemVlNS5jb20iLCJuYmYiOjE2Njk4MDY4OTJ9.Qx2LvhnN6nsFhTNVkb0y999OUv901wx35C5PihbaPpvLr7e9KE3KxJmqDmlaiPDOZi1kIeL7lxzw5FEBspFlxd6BTCf-5amMW0KMmmZpvLh83Ouw0z2aqslMREG4BGwVDgrLvl8325EtW1m9-femN3vNzdgMMnRTIIrVm8D7NUVuInfZUkrgIEgKhH0nBYy674iVOdRrZUvS1ZSY0Hf0YChe0Eosu-qWwla_T9QCg_AjTGNZaMD1StwjuVwEZHb06t3O0lbGu5B1y_3BXA2nJtQ6Ol52XFMDQk8fG21aogRWJnjyqWckP6UEWM_steWr73XjHXq31vuQeswB6HsGLQ"

# headers.update({'Authorization': auth})

get_user()


def get_code():
    url = "https://useraction.zee5.com/device/v2/getcode.php"
    body = {"identifier": "pwa", "partner": "zee5",
            "authorization": headers["Authorization"]}

    body = dumps(body)
    jd = requests.post(url, headers=headers, data=body).json()
    devid = str(uuid.UUID(jd.get('token')))
    return devid


country = headers['country'] if headers.get('country') else 'IN'
country = 'IN'


def clear_cache():
    """
    Clear the cache database.
    """

    msg = 'Cached Data has been cleared'
    cache.table_name = 'zee5'
    cache.cacheDelete('%get%')
    addon.setSetting("Authorization", "")
    xbmc.executebuiltin('Notification(%s, %s, %d, %s)' %
                        (_addonname, msg, 3000, _icon))


def get_genre(item):

    if not item:
        return 'ALL'

    genres = set()
    for genreField in ['genre', 'genres']:
        data = item.get(genreField)
        if not data:
            continue
        genres.update(map(operator.itemgetter('value'), data))

    return ",".join(list(genres)) if genres else 'ALL'


def go_page(sid, Stype, total):
    """
    kb = xbmc.Keyboard('', 'Search Page')
    kb.doModal()  # Onscreen keyboard appears
    if not kb.isConfirmed():
        return
    page=int(kb.getText())-1
    """
    pnum = xbmcgui.Dialog().numeric(0, 'Enter Page Number')
    # page=int(page)-1
    if int(pnum) > int(total):
        pnum = total
    if Stype == 'Episode':
        list_episodes(sid, pnum)
    elif Stype == 'Show':
        list_shows(sid, pnum)
    else:
        list_season(sid, pnum, Stype)
    # User input
    return


def get_user_input():
    kb = xbmc.Keyboard(
        '', 'Search for Movies/TV Shows/Trailers/Videos in all languages')
    kb.doModal()  # Onscreen keyboard appears
    if not kb.isConfirmed():
        return

    # User input
    return kb.getText()


def get_search(query, page):
    """
    Get the list of shows.
    :return: list
    """

    url = 'https://contentapi.zee5.com/content/search?q={}&limit={}&page={}&country={}&translation=en&version=8&languages={}&filters='.format(
        urllib_parse.quote_plus(query),
        ITEMS_LIMIT,
        page,
        country,
        languages
    )
    data = requests.get(url, headers=headers).json()
    if not data.get('total_count'):
        kodiutils.notification('No Search Results',
                               'No item found for {}'.format(query))
        return
    listing = []

    for item in data['results']:
        title = item['title']
        sid = item['id']
        mediatype = item['contentType']
        image = item['image_url']
        icon = {'poster': image,
                'icon': image,
                'thumb': image,
                'fanart': image}
        labels = {'title': title,
                  'genre': get_genre(item),
                  'year': item.get('release_date')[:4] if item.get('release_date') else None,
                  'aired': item.get('release_date')[:10] if item.get('release_date') else None,
                  'duration': item.get('duration') if item.get('duration') else None,
                  'mediatype': 'video'
                  }

        listing.append((title, icon, labels, sid, mediatype, page))

    page = int(page)
    totals = int(data['total_count'])
    itemsleft = totals - page * 10
    finalpg = True
    if itemsleft > 0:
        finalpg = False
        pages = int(math.ceil(totals / 10.0))

    if not finalpg:
        page += 1
        title = 'Next Page.. (Currently in Page %s of %s)' % (page, pages)
        labels = {}
        icon = {'poster': _icon,
                'icon': _icon,
                'thumb': _icon,
                'fanart': _fanart}
        listing.append((title, icon, labels, sid, mediatype, page))
    return listing


def list_search(query, page):
    """
    Create the list of channels in the Kodi interface.
    """

    if page == '0':
        query = get_user_input()
        if not query:
            return []

    # shows = cache.cacheFunction(get_search,query)
    shows = get_search(query, page)
    listing = []

    for title, icon, labels, sid, stype, pnum in shows:
        list_item = xbmcgui.ListItem(label='[COLOR yellow]%s[/COLOR]' % title)
        list_item.setArt(icon)
        list_item.setInfo('video', labels)
        # list_item.setProperty('IsPlayable', 'false')

        if 'Next Page' in title:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=search&query={1}&page={2}'.format(
                _url, query, pnum)
            is_folder = True
        elif stype in ['Show']:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=list_season&sid={1}&page=1&showtype={2}'.format(
                _url, sid, stype)
            is_folder = True
        else:
            list_item.setProperty('IsPlayable', 'true')
            if stype == 'TV Channel':
                url = '{0}?action=playNew&vid={1}&sid={2}&itemtype=LIVE'.format(
                    _url, sid, sid)
            else:
                url = '{0}?action=playNew&vid={1}&sid={2}&itemtype=MOVIE'.format(
                    _url, sid, sid)
            is_folder = False
        listing.append((url, list_item, is_folder))

    """
            if mediatype in ['movie','video','clip','trailer','episode']:
            list_item.setProperty('IsPlayable', 'true')
            url = '{0}?action=playNew&vid={1}&sid={2}&itemtype=MOVIE'.format(_url,eid,eid)
            is_folder = False
            xbmcplugin.setContent(_handle, 'movies')
        elif mediatype=='tvshow':
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=list_season&sid={1}&page=1&showtype={2}'.format(_url,eid,mediatype)
            is_folder = True
        else:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=list_season&sid={1}&page=1'.format(_url,eid)
            is_folder = True
    """

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.setContent(_handle, 'episodes')
    xbmcplugin.endOfDirectory(_handle)


def get_top():

    top = []
    menu_group = "navMenuPortal"
    menu_lang = "tamil,telugu,malayalam,kannada,bengali,marathi"
    # url = 'https://b2bapi.zee5.com/front/countrylist.php?lang=en&ccode={}'.format(
    # country)
    url ="https://pwaapi.sunnxt.com/content/v2/carousel/_info?group={}&language={}".format(
        menu_group, menu_lang
        )
    data = requests.get(url, headers=headers).json()

    menus = data['results']
    for menu in menus:
        title = menu['title']
        cid =  menu['actionUrl']
        if title != 'Play5':
            top.append((title, cid))

    title = 'Refresh'
    cid = 1
    top.append((title, cid))
    title = 'Search'
    cid = 2
    top.append((title, cid))
    title = 'Clear Cache'
    cid = 3
    top.append((title, cid))
    return top


def get_channels(lang, cid, page):
    """
    Get the list of channels.
    :return: list
    """
    channels = []
    url = 'https://pwaapi.sunnxt.com/content/v2/contentList?type={type}&fields={fields}&startIndex={startIndex}&count=100&orderBy=siblingOrder&orderMode=1&language={language}'.format(
        type=cid,
        fields='contents,images,generalInfo,publishingHouse,relatedMedia,relatedCast,subtitles,relatedMedia,relatedMultimedia',
        startIndex=page,
        language=lang
    )
    data = requests.get(url, headers=headers).json()

    for bucket in data['results'] or []:

        # Skip buckets without any items.
        if not bucket.get('_id'):
            continue

        icon = {'poster': bucket['images']['values'][-1].get('link'),
                'icon': bucket['images']['values'][-4].get('link'),
                'thumb': bucket['images']['values'][-3].get('link'),
                'fanart': bucket['images']['values'][-2].get('link')}

        bid = bucket['_id']
        title = bucket['title']
        asset_subtype = bucket['generalInfo'].get('type')
        labels = {'title': title,
                  'plot': bucket['generalInfo'].get('description')
                  }
        channels.append((title, icon, bid, labels, asset_subtype))

    #
    """
    page = int(page)
    totals = int(data['total'])
    itemsleft = totals - page * 10

    finalpg = True
    if itemsleft > 0:
        finalpg = False
        pages = int(math.ceil(totals / 10.0))

    if not finalpg:
        title = 'Next Page.. (Currently in Page %s of %s)' % (page, pages)
        page += 1
        icon = {'poster': _icon,
                'icon': _icon,
                'thumb': _icon,
                'fanart': _fanart}
        labels = {}
        channels.append((title, icon, page, labels, ''))
    """

    return channels



def old_get_channels(cid, page):
    """
    Get the list of channels.
    :return: list
    """
    channels = []
    url = 'https://gwapi.zee5.com/content/collection/{id}?country={country}&page={page}&limit={limit}&translation=en&item_limit=10&languages={lang}&version=10'.format(
        id=cid,
        country=country,
        page=page,
        limit=ITEMS_LIMIT,
        lang=languages
    )
    data = requests.get(url, headers=headers).json()

    for bucket in data['buckets'] or []:

        # Skip buckets without any items.
        if not bucket.get('items'):
            continue

        icon = {'poster': bucket['items'][0]['image_url'].get('list'),
                'icon': bucket['items'][0]['image_url'].get('list'),
                'thumb': bucket['items'][0]['image_url'].get('list'),
                'fanart': bucket['items'][0]['image_url'].get('cover')}

        bid = bucket['id']
        title = bucket['title']
        asset_subtype = bucket['asset_subtype']
        labels = {'title': title,
                  'plot': bucket.get('description')
                  }
        channels.append((title, icon, bid, labels, asset_subtype))

    #
    page = int(page)
    totals = int(data['total'])
    itemsleft = totals - page * 10

    finalpg = True
    if itemsleft > 0:
        finalpg = False
        pages = int(math.ceil(totals / 10.0))

    if not finalpg:
        title = 'Next Page.. (Currently in Page %s of %s)' % (page, pages)
        page += 1
        icon = {'poster': _icon,
                'icon': _icon,
                'thumb': _icon,
                'fanart': _fanart}
        labels = {}
        channels.append((title, icon, page, labels, ''))

    return channels


def get_stream_url(show_id, stream_hash):

    channel_data = get_channel_data(show_id)

    if channel_data:
        stream_base_url =  "https://suntvlive.akamaized.net/hls/live"
        stream_url = "{stream_base_url}/{stream_id}/{stream_name}/{stream_hash}/master_{res}.m3u8".format(
            stream_base_url=stream_base_url,
            stream_id=channel_data['stream_id'],
            stream_name=channel_data['stream_name'],
            stream_hash=stream_hash,
            res=channel_data['resolution']
        )

        return stream_url

    return None


def get_ts_url(show_id, stream_index, ts_index):

    stream_hash = addon.getSetting("hdntl")

    channel_data = get_channel_data(show_id)

    stream_base_url =  "https://suntvlive.akamaized.net/hls/live"
    ts_url = ""

    if channel_data:
        ts_url = "/".join([ stream_base_url,
                          channel_data['stream_id'],
                          channel_data['stream_name'],
                          stream_hash,
                          channel_data['stream_folder'],
                          'master_' + channel_data['resolution'],
                          '%05d' % (stream_index),
                          'master_%s_%05d.ts' % (channel_data['resolution'], ts_index)
        ])

    return ts_url


def update_db_stream_folder_index(show_id, stream_url):

    stream_folder, stream_index, ts_index = (None, None, None)

    response = requests.get(stream_url, headers=headers)
    stream_data =  response.text.strip().split('\n')[-1].split('/')

    stream_folder = stream_data[0]
    stream_index = stream_data[2]
    ts_index = stream_data[-1].split('.')[0].split('_')[-1]

    conn = sqlite3.connect(channeldb)
    conn.row_factory = sqlite3.Row
    conn.text_factory = str
    c = conn.cursor()

    try:
        c.execute("UPDATE channel SET stream_folder='{}',stream_index={},ts_index={} WHERE channel_id={}".format(
            stream_folder,
            stream_index,
            ts_index,
            show_id))
        conn.commit()
        conn.close()
    except:
        conn.close()

    return (stream_folder, stream_index, ts_index)


def refresh():

    # show_id for Sun News = 38926
    show_id = 38926

    media_url = get_media_url(show_id)
    stream_hash = get_stream_hash(media_url)
    addon.setSetting("hdntl", stream_hash)


def check_and_refresh():

    now = datetime.now()
    hdntl = addon.getSetting("hdntl")

    if len(hdntl) < 100:
        # If hdntl doesn't exists or not of required len, call refresh
        return refresh()

    now_timestamp = int(datetime.timestamp(now))
    hdntl_timestamp = int(hdntl.split('~')[0].split('=')[-1])

    if hdntl_timestamp - now_timestamp < 1000:
        # Update hdntl if only 1000 seconds to hdntl expiry
        refresh()


def get_stream_hash(media_url):

     response = requests.get(media_url, headers=headers)
     addon.setSetting('User-Agent', headers['user-agent'])
     return response.text.strip().split('\n')[-1].split('/')[0]


def get_media_url(showid):

    fields = "contents,user/currentdata,images,generalInfo,subtitles,relatedCast,globalServiceName,globalServiceId,relatedMedia,videos,thumbnailSeekPreview"

    headers['Cookie'] = "sessionid=" +  addon.getSetting("SessionID")

    url = 'https://www.sunnxt.com/next/api/media/{id}?playbackCounter=1&fields={fields}&licenseType=false'.format(
        id=showid,
        fields=fields)


    data = requests.get(url, headers=headers).json()
    response = aes.decrypt(data['response'])

    body = loads(response)

    video_link = None

    if body['status'] == 'SUCCESS':
        result = body['results'][0]
        video = result['videos']
        if video['status'] == 'ERR_GUEST_USER':
            # xbmcgui.Dialog().ok(addon.getAddonInfo('name'), video['message'])
            login()
            headers['Cookie'] = "sessionid=" +  addon.getSetting("SessionID")

            data = requests.get(url, headers=headers).json()
            response = aes.decrypt(data['response'])

            body = loads(response)

            if body['status'] == 'SUCCESS':
                result = body['results'][0]
                video = result['videos']
                if video['status'] == 'SUCCESS':
                    video_link = video['values'][0]['link']
                    # xbmcgui.Dialog().ok(addon.getAddonInfo('name'), video_link)
        elif video['status'] == 'SUCCESS':
            video_link = video['values'][0]['link']
        else:
            video_link = None

    return video_link


def get_shows(showid, page):
    """
    Get the list of shows.
    :return: list
    """
    shows = []

    """
        Code that works to fetch video_link (hdnea) for Sun-News Only
    """

    """
    fields = "contents,user/currentdata,images,generalInfo,subtitles,relatedCast,globalServiceName,globalServiceId,relatedMedia,videos,thumbnailSeekPreview"

    url = 'https://www.sunnxt.com/next/api/media/{id}?playbackCounter=1&fields={fields}&licenseType=false'.format(
        id=showid,
        fields=fields)

    # url = 'https://gwapi.zee5.com/content/collection/{id}?country={country}&page={page}&limit={limit}&languages={lang}&translation=en&version=10'.format(
    #     id=showid,
    #     country=country,
    #     page=page,
    #     limit=ITEMS_LIMIT, lang=languages)

    data = requests.get(url, headers=headers).json()
    response = aes.decrypt(data['response'])

    body = loads(response)

    result = None

    if body['status'] == 'SUCCESS':
        result = body['results'][0]
        video = result['videos']
        if video['status'] == 'ERR_GUEST_USER':
            # xbmcgui.Dialog().ok(addon.getAddonInfo('name'), video['message'])
            login()
            headers['Cookie'] = "sessionid=" +  addon.getSetting("SessionID")

            data = requests.get(url, headers=headers).json()
            response = aes.decrypt(data['response'])

            body = loads(response)

            if body['status'] == 'SUCCESS':
                result = body['results'][0]
                video = result['videos']
                if video['status'] == 'SUCCESS':
                    video_link = video['values'][0]['link']
                    xbmcgui.Dialog().ok(addon.getAddonInfo('name'), video_link)

    # web_pdb.set_trace()
    page = 1
    pages = 1
    if result:
        if result['video']['status'] == 'SUCCESS':
            title = result['generalInfo']['title']
            content_id = result['video']['values'][0]['link']
            labels = {}
            icon = {'poster': _icon,
                    'icon': _icon,
                    'thumb': _icon,
                    'fanart': _fanart}
            shows.append((title, icon, content_id, page, labels, pages))
    """


    ## xbmc.log(dumps(data))
    #seasons = data['buckets'][0]['items']
    #for season in seasons:
    #    # title=season['title'].encode('utf-8')
    #    title = season['title']
    #    description = season.get('description')

    #    if season['asset_type'] == 9:
    #        stype = 'live'
    #        #
    #    else:
    #        stype = season['asset_subtype']

    #    if stype == 'external_link':
    #        stype = season['slug'].split(
    #            '/')[3] if season['slug'][:4] == 'http' else season['slug'].split('/')[0]
    #        stype = stype[:-1]
    #        content_id = season['slug'].rsplit('/', 2)[1] if season['slug'].rsplit(
    #            '/', 1)[1] == 'latest1' else season['slug'].rsplit('/', 1)[1]
    #        show_id = season['id'] if season.get('id') else content_id
    #        """
    #        if season['asset_type']==101:
    #            show_id=season['slug'].rsplit('/', 1)[1]
    #            #stype='live'
    #        else:
    #            show_id=season['slug'].rsplit('/', 2)[1]
    #            #stype='tvshow'
    #        """
    #    else:
    #        content_id = season['id']
    #        show_id = season['tvshow'].get(
    #            'id') if season.get('tvshow') else content_id
    #    if stype in ['movie', 'video', 'clip', 'episode', 'live', 'channel', 'collection', 'trailer']:
    #        mediatype = 'movie'
    #    else:
    #        mediatype = 'tvshow'
    #    labels = {'title': title,
    #              'genre': get_genre(season),
    #              'castandrole': season['actors'] if season.get('actors') else [],
    #              'plot': description,
    #              'year': season.get('release_date')[:4] if season.get('release_date') else None,
    #              'aired': season.get('release_date')[:10] if season.get('release_date') else None,
    #              'duration': season.get('duration') if season.get('duration') else None,
    #              'mediatype': mediatype
    #              }
    #    icon = {'poster': season['image_url'].get('list'),
    #            'icon': season['image_url'].get('list'),
    #            'thumb': season['image_url'].get('list'),
    #            'fanart': season['image_url'].get('cover')
    #            }

    #    shows.append((title, icon, content_id, show_id, labels, stype))

    # page = int(page)
    # totals = int(data['total'])
    # itemsleft = totals - page * 10
    # finalpg = True
    # if itemsleft > 0:
        # finalpg = False
        # pages = int(math.ceil(totals / 10.0))

    # if not finalpg:
        # title = 'Next Page.. (Currently in Page %s of %s)' % (page, pages)
        # page += 1
        # labels = {}
        # icon = {'poster': _icon,
        #         'icon': _icon,
        #         'thumb': _icon,
        #         'fanart': _fanart}
        # shows.append((title, icon, content_id, page, labels, pages))
        # title = "Go Page..."
        # shows.append((title, icon, content_id, page, labels, pages))

    return shows


def get_season(season_id, page, showtype):
    """
    Get the list of episodes.
    :return: list
    """
    season = []
    if showtype == 'Manual':
        stype = 'collection'
    else:
        stype = 'tvshow'
    url = 'https://gwapi.zee5.com/content/{stype}/{id}?country={country}&page={page}&limit={limit}&languages={lang}&version=10'.format(
        stype=stype,
        id=season_id,
        country=country,
        page=page,
        limit=ITEMS_LIMIT,
        lang=languages
    )
    data = requests.get(url, headers=headers).json()
    if showtype == 'Manual':
        seasons = data['buckets'][0]['items']
    else:
        seasons = data['seasons']
    for show in seasons:
        if showtype == 'Manual':
            subtype = show.get('asset_subtype')
            rdate = show.get('release_date')[:10] if show.get(
                'release_date') else None
            image1 = show['image_url'].get('cover')
            image2 = show['image_url'].get('list')
            desc = show.get('description')
        else:
            subtype = data.get('asset_subtype')
            rdate = data.get('release_date')[:10] if data.get(
                'release_date') else None
            image1 = data.get('image_url')
            image2 = data.get('image_url')
            desc = data.get('description')

        if subtype in ['movie', 'video', 'clip', 'webisode', 'trailer']:
            mediatype = 'movie'
            if not image1:
                image1 = data.get('image_url')
                image2 = data.get('image_url')
        else:
            mediatype = 'tvshow'

        sid = show.get('id')
        stitle = show.get('title')

        labels = {'title': stitle,
                  'genre': get_genre(data),
                  'mediatype': mediatype,
                  'plot': desc,
                  'aired': rdate,
                  }

        icon = {'poster': image1,
                'icon': image2,
                'thumb': image2,
                'fanart': image2}

        season.append((stitle, icon, sid, labels, subtype))

    if showtype == 'Manual':
        page = int(page)
        totals = int(data['total'])
        itemsleft = totals - page * 10
        finalpg = True
        if itemsleft > 0:
            finalpg = False
            pages = int(math.ceil(totals / 10.0))

        if not finalpg:
            stitle = 'Next Page.. (Currently in Page %s of %s)' % (page, pages)
            page += 1
            labels = {}
            icon = {'poster': _icon,
                    'icon': _icon,
                    'thumb': _icon,
                    'fanart': _fanart}
            season.append((stitle, icon, page, labels, pages))
            stitle = "Go Page..."
            season.append((stitle, icon, page, labels, pages))
    return season


def get_episodes(episodeid, page):
    """
    Get the list of episodes.
    :return: list
    """
    episodes = []
    page = int(page)

    url = 'https://gwapi.zee5.com/content/tvshow/?season_id={id}&type=episode&translation=en&country={country}&on_air=true&asset_subtype=tvshow&page={page}&limit={limit}'.format(
        id=episodeid,
        country=country,
        page=page,
        limit=ITEMS_LIMIT
    )

    data = requests.get(url, headers=headers).json()
    items = data['episode']
    for item in items:
        etitle = 'Episodes {} - {}'.format(item.get('episode_number'), six.ensure_str(
            item.get('title'), encoding='utf-8', errors='strict'))
        eid = item.get('id')
        showid = item['tvshow'].get('id')

        plot = item.get('description')
        eptype = item.get('asset_subtype')
        labels = {'title': etitle,
                  'genre': get_genre(item),
                  'plot': plot,
                  'duration': item.get('duration'),
                  'episode': item.get('episode_number'),
                  'tvshowtitle': etitle,
                  'year': item.get('release_date')[:4],
                  'aired': item.get('release_date')[:10],
                  'mediatype': 'episode'
                  }
        fanart = item['image_url']
        poster = item['image_url']
        icon = item['image_url']
        thumb = item['image_url']

        icon = {'poster': poster,
                'icon': icon,
                'thumb': thumb,
                'fanart': fanart}

        episodes.append((etitle, eid, icon, labels, eptype, showid))
    total = data['total']

    balcount = int(total) - page * 10
    if balcount > 0:
        # pages=int(total)/10
        pages, mod = divmod(int(total), 10)

        pages = pages + 1 if mod > 0 else pages
        etitle = 'Next Page... (Page %s of %s)' % (page, pages)
        page += 1
        labels = {}
        icon = {'poster': _icon,
                'icon': _icon,
                'thumb': _icon,
                'fanart': _fanart}
        episodes.append((etitle, page, icon, labels, eptype, showid))

        etitle = 'Go Page...'
        labels = {}
        icon = {'poster': _icon,
                'icon': _icon,
                'thumb': _icon,
                'fanart': fanart}
        episodes.append((etitle, page, icon, labels, eptype, pages))

    return episodes


def list_top():
    """
    Create the list of countries in the Kodi interface.
    """

    items = get_top()
    listing = []
    for title, cid in items:
        list_item = xbmcgui.ListItem(label=title)
        if 'Search' in title:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=search&query=FIRST&page=0'.format(_url)
            is_folder = True
        elif 'Refresh' in title:
            list_item.setProperty('IsPlayable', 'true')
            url = '{0}?action=refresh'.format(_url)
            is_folder = False
        elif 'Clear Cache' in title:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=clear_cache'.format(_url)
            is_folder = True
        elif 'Live TV' in title:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=list_live'.format(_url)
            is_folder = True
            list_item.setArt({'poster': _icon,
                              'icon': _icon,
                              'thumb': _icon,
                              'fanart': _fanart})
        else:
            list_item.setInfo('video', {'title': title})
            list_item.setProperty('IsPlayable', 'false')
            list_item.setArt({'poster': _icon,
                              'icon': _icon,
                              'thumb': _icon,
                              'fanart': _fanart})
            url = '{0}?action=list_item&cid={1}&page=1'.format(_url, cid)
            is_folder = True
        listing.append((url, list_item, is_folder))

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    # xbmcplugin.setContent(_handle, 'addons')
    xbmcplugin.endOfDirectory(_handle)


def list_channels(lang, cid, page):
    """
    Create the list of countries in the Kodi interface.
    """

    channels = cache.cacheFunction(get_channels, lang, cid, page)
    listing = []

    # web_pdb.set_trace()
    for title, icon, bid, labels, subtype in channels:
        list_item = xbmcgui.ListItem(label='[COLOR yellow]%s[/COLOR]' % title)
        if 'Next Page' in title:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=list_item&cid={1}&page={2}'.format(
                _url, cid, bid)
            is_folder = True
        else:
            list_item.setProperty('IsPlayable', 'true')
            list_item.setArt(icon)
            list_item.setInfo('video', labels)
            url = '{0}?action=playLive&showid={1}&page=1'.format(_url, bid)
            is_folder = False
        # else:
        #     list_item.setProperty('IsPlayable', 'false')
        #     list_item.setArt(icon)
        #     list_item.setInfo('video', labels)
        #     url = '{0}?action=list_shows&showid={1}&page=1'.format(_url, bid)
        #     is_folder = True
        listing.append((url, list_item, is_folder))

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    # xbmcplugin.setContent(_handle, 'addons')
    xbmcplugin.endOfDirectory(_handle)


def list_shows(showid, page):
    """
    Create the list of channels in the Kodi interface.
    """

    shows = cache.cacheFunction(get_shows, showid, page)
    listing = []
    for title, icon, cid, sid, labels, stype in shows:
        list_item = xbmcgui.ListItem(label='[COLOR yellow]%s[/COLOR]' % title)
        list_item.setArt(icon)
        list_item.setInfo('video', labels)

        if 'Next Page' in title:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=list_shows&showid={1}&page={2}'.format(
                _url, showid, sid)
            is_folder = True
        elif "Go Page" in title:
            list_item.setProperty("IsPlayable", "false")
            url = "{0}?action=gopage&sid={1}&Stype={2}&total={3}".format(_url, showid, 'Show', stype)
            is_folder = True
        else:
            if stype in ['video', 'clip', 'episode', 'webisode', 'collection', 'trailer']:
                list_item.setProperty('IsPlayable', 'true')
                url = '{0}?action=playNew&vid={1}&sid={2}&itemtype=EPISODE'.format(
                    _url, cid, sid)
                is_folder = False
                xbmcplugin.setContent(_handle, 'episodes')
            elif stype in ['movie']:
                list_item.setProperty('IsPlayable', 'true')
                url = '{0}?action=playNew&vid={1}&sid={2}&itemtype=MOVIE'.format(
                    _url, cid, sid)
                is_folder = False
                xbmcplugin.setContent(_handle, 'movies')
            elif stype in ['live', 'channel']:
                list_item.setProperty('IsPlayable', 'true')
                url = '{0}?action=playNew&vid={1}&sid={2}&itemtype=LIVE'.format(
                    _url, cid, sid)
                is_folder = False
            else:
                list_item.setProperty('IsPlayable', 'false')
                url = '{0}?action=list_season&sid={1}&page=1&showtype={2}'.format(
                    _url, cid, stype)
                is_folder = True
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    # xbmcplugin.setContent(_handle, 'episodes')
    xbmcplugin.endOfDirectory(_handle)


def list_season(seasonid, page, showtype):
    """
    Create the list of channels in the Kodi interface.
    """
    shows = cache.cacheFunction(get_season, seasonid, page, showtype)
    listing = []

    for title, icon, sid, labels, stype in shows:
        list_item = xbmcgui.ListItem(label='[COLOR yellow]%s[/COLOR]' % title)

        list_item.setArt(icon)
        list_item.setInfo('video', labels)
        if 'Next Page' in title:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=list_season&sid={1}&page={2}&showtype={3}'.format(
                _url, seasonid, sid, showtype)
            is_folder = True
        elif "Go Page" in title:
            list_item.setProperty("IsPlayable", "false")
            url = "{0}?action=gopage&sid={1}&Stype={2}&total={3}".format(_url, seasonid, showtype, stype)
            is_folder = True
        else:
            if stype in ['movie', 'video', 'clip', 'webisode', 'trailer']:
                list_item.setProperty('IsPlayable', 'true')
                url = '{0}?action=playNew&vid={1}&sid={2}&itemtype=EPISODE'.format(
                    _url, sid, seasonid)
                is_folder = False
                xbmcplugin.setContent(_handle, 'movie')
            else:
                list_item.setProperty('IsPlayable', 'false')
                url = '{0}?action=list_episodes&sid={1}&page=1'.format(
                    _url, sid)
                is_folder = True
        listing.append((url, list_item, is_folder))

    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)


def list_episodes(eid, page):
    """
    Create the list of episodes in the Kodi interface.
    """
    episodes = cache.cacheFunction(get_episodes, eid, page)
    listing = []

    for etitle, epid, icon, labels, eptype, showid in episodes:
        list_item = xbmcgui.ListItem(label=etitle)
        list_item.setArt(icon)
        list_item.setInfo('video', labels)
        if 'Next Page' in etitle:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=list_episodes&sid={1}&page={2}'.format(
                _url, eid, epid)
            is_folder = True
        elif 'Go Page' in etitle:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=gopage&sid={1}&Stype={2}&total={3}'.format(
                _url, eid, 'Episode', showid)
            is_folder = True
        else:
            list_item.setProperty('IsPlayable', 'true')
            url = '{0}?action=playNew&vid={1}&sid={2}&itemtype=EPISODE'.format(
                _url, epid, showid)
            is_folder = False
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.setContent(_handle, 'episodes')
    xbmcplugin.endOfDirectory(_handle)


def list_by_language(cid):

    channels = [('Tamil', 'tamil'), ('Telugu', 'telugu'), ('Malayalam', 'malayalam'),
                ('Kannada', 'kannada'), ('Marathi', 'marathi'), ('Bengali', 'bengali')]
    listing = []

    for title, lid in channels:

        list_item = xbmcgui.ListItem(label='[COLOR yellow]%s[/COLOR]' % title)
        list_item.setProperty('IsPlayable', 'false')
        url = '{0}?action=list_channel_by_language&language={1}&cid={2}&page=1'.format(_url, lid, cid)
        is_folder = True
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)


def list_live():

    channels = [('Entertainment', 'Entertainment'), ('News', 'News'), ('Movies', 'Movie'),
                ('Music', 'Music'), ('Devotional', 'Devotional'), ('Lifestyle', 'Lifestyle')]
    # , 0-8-5852('Religious'), ('Food'), ('Infotainment'), ('Lifestyle'), ('Sports')
    listing = []

    for title, lid in channels:

        list_item = xbmcgui.ListItem(label='[COLOR yellow]%s[/COLOR]' % title)
        list_item.setProperty('IsPlayable', 'false')
        url = '{0}?action=list_livechannel&channelid={1}&page=1'.format(_url, lid)
        is_folder = True
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    xbmcplugin.endOfDirectory(_handle)


def get_livechannel(channelid, page):
    """
    Get the list of shows.
    :return: list
    """
    shows = []

    url = 'https://gwapi.zee5.com/v1/channel/bygenre?sort_by_field=mostwatched&sort_order=desc&genres={genres}&languages={lang}&country={country}&translation=en&platform=PWA&page={page}&limit={limit}'.format(
        genres=channelid,
        country=country,
        page=page,
        limit=ITEMS_LIMIT,
        lang=languages)

    data = requests.get(url, headers=headers).json()
    # xbmc.log(dumps(data))
    channels = data['items'][0]['items']
    for channel in channels:
        # title=season['title'].encode('utf-8')
        title = channel['title']
        stype = 'live'
        content_id = channel['id']
        mediatype = 'movie'
        labels = {'title': title,
                  'genre': get_genre(channel),
                  'mediatype': mediatype
                  }
        img = 'https://akamaividz.zee5.com/resources/%s/list/170x170/%s' % (channel.get('id'), channel.get('list_image'))
        icon = {'poster': img,
                'icon': img,
                'thumb': img,
                'fanart': img
                }
        shows.append((title, icon, content_id, labels, stype))
    """
    page = int(page)
    totals = int(data['total'])
    itemsleft = totals - page * 10
    finalpg = True
    if itemsleft > 0:
        finalpg = False
        pages = int(math.ceil(totals / 10.0))

    if not finalpg:
        title = 'Next Page.. (Currently in Page %s of %s)' % (page, pages)
        page += 1
        labels = {}
        icon = {'poster': _icon,
                'icon': _icon,
                'thumb': _icon,
                'fanart': _fanart}
        shows.append((title, icon, page, labels, ''))
    """
    return shows


def list_livechannel(channelid, page):
    """
    Create the list of channels in the Kodi interface.
    """

    shows = cache.cacheFunction(get_livechannel, channelid, page)
    listing = []

    for title, icon, cid, labels, stype in shows:
        list_item = xbmcgui.ListItem(label='[COLOR yellow]%s[/COLOR]' % title)
        list_item.setArt(icon)
        list_item.setInfo('video', labels)

        if 'Next Page' in title:
            list_item.setProperty('IsPlayable', 'false')
            url = '{0}?action=list_livechannel&channelid={1}&page={2}'.format(
                _url, channelid, cid)
            is_folder = True
        else:
            list_item.setProperty('IsPlayable', 'true')
            url = '{0}?action=playNew&vid={1}&sid={2}&itemtype=LIVE'.format(
                _url, cid, channelid)
            is_folder = False
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle, listing, len(listing))
    # xbmcplugin.setContent(_handle, 'episodes')
    xbmcplugin.endOfDirectory(_handle)


def playLive(show_id):

        # Pass the item to the Kodi player.

        # Update hdntl on expiry (When it is 1000 seconds to go)
        check_and_refresh()

        stream_hash = addon.getSetting("hdntl")
        stream_url = get_stream_url(show_id, stream_hash)

        # For archive playing
        # update_stream_folder_index(show_id, stream_url)

        # web_pdb.set_trace()
        # xbmcgui.Dialog().ok(addon.getAddonInfo('name'), stream_url)

        vidUrl = "{}|User-Agent={}&Content-Type=video/mp4".format(
            stream_url,
            USER_AGENT
        ).strip()

        play_item = xbmcgui.ListItem(path=vidUrl)
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def playBack(show_id, rewind_index):

    stream_hash = addon.getSetting("hdntl")
    stream_url = get_stream_url(show_id, stream_hash)

    # For archive playing
    (stream_folder, stream_index, ts_index) = update_db_stream_folder_index(show_id, stream_url)


    stream_index = int(stream_index) - int(rewind_index)
    ts_end = ts_index if rewind_index == 0 else 1800

    m3u8_header = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:6\n"
    m3u8_header += "#EXT-X-MEDIA-SEQUENCE:1313032\n#EXT-X-DISCONTINUITY-SEQUENCE:13\n"
    m3u8_header += "#EXT-X-PROGRAM-DATE-TIME:2024-02-19T09:39:48.760Z"

    ts_urls = []
    # ts_urls.append(m3u8_header)
    for ts in range(1, ts_end):
        # ts_urls.append("#EXTINF:6.00000,")
        ts_urls.append(get_ts_url(show_id, stream_index, ts))

    # web_pdb.set_trace()
    # m3u8_file = os.path.join(profileDir, "playback.m3u8")
    # with open(m3u8_file, "w") as output_file:
    #     output_file.write("\n".join(ts_urls))

    # xbmcgui.Dialog().ok(addon.getAddonInfo('name'), stream_url)

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()

    for ts_url in ts_urls:
        vidUrl = "{}|User-Agent={}&Content-Type=application/x-mpegURL".format(
            ts_url,
            USER_AGENT
        ).strip()
        playlist.add(vidUrl, xbmcgui.ListItem(), index=-1)

    # vidUrl = "{}|User-Agent={}&Content-Type=application/x-mpegURL".format(
    #     m3u8_file,
    #     USER_AGENT
    # ).strip()


    # play_item.setProperty('inputstream.adaptive.max_bandwidth', '1000000')

    # hdr = "user-agent=%s" % USER_AGENT
    # play_item.setProperty('inputstream.adaptive.stream_headers', hdr)

    # playlist.setContentLookup(False)

    xbmc.Player().play(playlist, windowed=False, startpos= -1)
    # xbmc.Player().play(playlist)


    # play_item = xbmcgui.ListItem(path=vidUrl)
    # xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def playNew(item_id, show_id, item_type):

    userid = headers.get('uid') if 'uid' in headers else ''

    # real_user_agent =xbmc.getUserAgent()

    if headers.get('Authorization'):
        if item_type == 'EPISODE':
            url = 'https://spapi.zee5.com/singlePlayback/getDetails/secure?content_id={}&show_id={}&device_id={}&platform_name={}&translation=en&user_language={}&country={}&app_version=2.51.26&user_type=register&check_parental_control=false&uid={}&ppid={}&version=12'.format(
                item_id, show_id, device_id, platform, languages, country, userid, device_id)
        elif item_type == 'MOVIE':
            url = 'https://spapi.zee5.com/singlePlayback/getDetails/secure?content_id={}&device_id={}&platform_name={}&translation=en&user_language={}&country={}&app_version=2.51.26&user_type=register&check_parental_control=false&uid={}&ppid={}&version=12'.format(
                item_id, device_id, platform, languages, country, userid, device_id)
        else:
            url = 'https://spapi.zee5.com/singlePlayback/getDetails/secure?channel_id={}&device_id={}&platform_name={}&translation=en&user_language={}&country={}&app_version=2.51.26&user_type=register&check_parental_control=false&uid={}&ppid={}&version=12'.format(
                item_id, device_id, platform, languages, country, userid, device_id)

        body = {"Authorization": headers.get(
            'Authorization'), "x-access-token": headers.get('x-access-token')}
    else:
        if item_type == 'EPISODE':
            url = 'https://spapi.zee5.com/singlePlayback/getDetails/secure?content_id={}&show_id={}&device_id={}&platform_name={}&translation=en&user_language={}&country={}&app_version=2.51.26&user_type=guest&check_parental_control=false&ppid={}&version=12'.format(
                item_id, show_id, device_id, platform, languages, country, device_id)
        elif item_type == 'MOVIE':
            url = 'https://spapi.zee5.com/singlePlayback/getDetails/secure?content_id={}&device_id={}&platform_name={}&translation=en&user_language={}&country={}&app_version=2.51.26&user_type=guest&check_parental_control=false&ppid={}&version=12'.format(
                item_id, device_id, platform, languages, country, device_id)
        else:
            url = 'https://spapi.zee5.com/singlePlayback/getDetails/secure?channel_id={}&show_id={}&device_id={}&platform_name={}&translation=en&user_language={}&country={}&app_version=2.51.26&user_type=guest&check_parental_control=false&ppid={}&version=12'.format(
                item_id, show_id, device_id, platform, languages, country, device_id)

        body = {"X-Z5-Guest-Token": device_id,
                "x-access-token": headers.get('x-access-token')}
    body = dumps(body)

    data = requests.post(url, headers=headers, data=body).json()

    if data.get('error_code') == '3608':
        if headers.get('Authorization'):
            add_device()
            data = requests.post(url, headers=headers, data=body).json()
    if data.get('error_msg'):
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)' %
                            (_addonname, data.get('error_msg'), 3000, _icon))
    else:
        """
        video_url = ""
        if not video_url:
            video_url = data['assetDetails'].get('hls_url') if data.get('assetDetails') else None
        if not video_url:
            video_url = data['keyOsDetails'].get('hls_token')
        if not video_url:
            video_url = data['keyOsDetails'].get('video_token')
        if not video_url and data['assetDetails'].get('video_url'):
            video_url = data['assetDetails']['video_url'].get('mpd')
        """
        url_list = []
        item_idx = 1
        if data['assetDetails'].get('hls_url'):
            url_list.append(("Stream %s" % item_idx, data['assetDetails'].get('hls_url')))
            item_idx += 1
        elif data['keyOsDetails'].get('hls_token'):
            url_list.append(("Stream %s" % item_idx, data['keyOsDetails'].get('hls_token')))
            item_idx += 1
        elif data['keyOsDetails'].get('video_token'):
            url_list.append(("Stream %s" % item_idx, data['keyOsDetails'].get('video_token')))
            item_idx += 1
        elif data['assetDetails'].get('video_url'):
            url_list.append(("Stream %s" % item_idx, data['assetDetails']['video_url'].get('m3u8')))
            item_idx += 1
        if data['assetDetails'].get('video_url'):
            url_list.append(("Stream %s" % item_idx, data['assetDetails']['video_url'].get('mpd')))
            item_idx += 1
        if item_idx == 2 or addon.getSetting('play_select') == 'Default':
            index = 0
        else:
            index = xbmcgui.Dialog().select("Playback Quality", [url[0] for url in url_list], preselect=0)

        video_url = url_list[index][1]

        customdata = data['keyOsDetails'].get('sdrm')
        nl = data['keyOsDetails'].get('nl')
        lic_url = 'https://spapi.zee5.com/widevine/getLicense'
        # lic_hdr = 'Content-Type=&customdata=%s&nl=%s' % (customdata, nl)
        lic_hdr = 'content-type=application/octet-stream&customdata=%s&nl=%s' % (customdata, nl)
        license_key = '%s|%s|R{SSM}|' % (lic_url, lic_hdr)

        play_item = xbmcgui.ListItem(path=video_url)

        # if data['assetDetails'].get('vtt_thumbnail_url'):
        # subtitles = data['assetDetails'].get('vtt_thumbnail_url').replace('thumbnails/index', 'manifest-en')
        # play_item.setSubtitles([subtitles])

        is_helper = inputstreamhelper.Helper('mpd', drm='widevine')

        if is_helper.check_inputstream():
            hdr = "user-agent=%s" % USER_AGENT

            if six.PY3:
                play_item.setProperty('inputstream', 'inputstream.adaptive')
            else:
                play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')

            play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')

            if (video_url.find('mpd') != -1):
                play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
                play_item.setMimeType('application/dash+xml')
                play_item.setProperty('inputstream.adaptive.license_key', license_key)

            elif (video_url.find('ism') != -1):
                play_item.setProperty('inputstream.adaptive.manifest_type', 'ism')
                play_item.setMimeType('application/vnd.ms-sstr+xml')
                play_item.setProperty('inputstream.adaptive.license_type', 'com.microsoft.playready')
            else:
                play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
                play_item.setMimeType('application/vnd.apple.mpegurl')

            if item_type == 'LIVE':
                play_item.setProperty('inputstream.adaptive.stream_headers', hdr)

            # play_item.setProperty('inputstream.adaptive.max_bandwidth', '1000000')
            # play_item.setProperty('inputstream.adaptive.stream_headers', hdr)
            play_item.setContentLookup(False)

        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring:
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(urllib_parse.parse_qsl(paramstring))
    # Check the parameters passed to the plugin


    if params:
        if params['action'] == 'list_item':
            list_by_language(params['cid'])
        elif params['action'] == 'list_channel_by_language':
            list_channels(params['language'], params['cid'], params['page'])
            # web_pdb.set_trace()
        elif params['action'] == 'list_shows':
            list_shows(params['showid'], params['page'])
        elif params['action'] == 'list_season':
            list_season(params['sid'], params['page'], params['showtype'])
        elif params['action'] == 'list_episodes':
            list_episodes(params['sid'], params['page'])
        elif params['action'] == 'playNew':
            playNew(params['vid'], params['sid'], params['itemtype'])
        elif params['action'] == 'playLive':
            playLive(params['showid'])
            # playBack(params['showid'],1)
        elif params['action'] == 'list_live':
            list_live()
        elif params['action'] == 'list_livechannel':
            list_livechannel(params['channelid'], params['page'])
        elif params['action'] == 'search':
            list_search(params['query'], params['page'])
        elif params['action'] == 'gopage':
            go_page(params['sid'], params['Stype'], params['total'])
        elif params['action'] == 'refresh':
            refresh()
        elif params['action'] == 'clear_cache':
            clear_cache()

    else:
        list_top()


def run():
    # Initial stuffs.
    kodiutils.cleanup_temp_dir()

    router(sys.argv[2][1:])
