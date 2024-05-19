# -*- coding: utf-8 -*-

from kodi_six import xbmc, xbmcaddon, xbmcgui, xbmcvfs
import logging
import json as json
import six
import os
from six.moves.urllib.request import urlopen

# read settings
ADDON = xbmcaddon.Addon()
if six.PY2:
    PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
    TEMP = xbmc.translatePath(os.path.join(PROFILE, 'temp', ''))
else:
    PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    TEMP = xbmcvfs.translatePath(os.path.join(PROFILE, 'temp', ''))

logger = logging.getLogger(__name__)


def notification(header, message, time=5000, icon=ADDON.getAddonInfo('icon'), sound=True):
    xbmcgui.Dialog().notification(header, message, icon, time, sound)


def show_settings():
    ADDON.openSettings()


def get_setting(setting):
    return ADDON.getSetting(setting).strip().decode('utf-8')


def set_setting(setting, value):
    ADDON.setSetting(setting, str(value))


def get_setting_as_bool(setting):
    return ADDON.getSettingBool(setting)


def get_setting_as_float(setting):
    try:
        return ADDON.getSettingNumber(setting)
    except ValueError:
        return 0


def get_setting_as_int(setting):
    try:
        return ADDON.getSettingInt(setting)
    except ValueError:
        return 0


def get_string(string_id):
    return ADDON.getLocalizedString(string_id).encode('utf-8', 'ignore')


def kodi_json_request(params):
    data = json.dumps(params)
    request = xbmc.executeJSONRPC(data)

    try:
        response = json.loads(request)
    except UnicodeDecodeError:
        response = json.loads(request.decode('utf-8', 'ignore'))

    try:
        if 'result' in response:
            return response['result']
        return None
    except KeyError:
        logger.warn("[{}] {}".format(params['method'], response['error']['message']))
        return None


def rmtree(path):
    if isinstance(path, str):
        path = path.encode('utf-8')

    dirs, files = xbmcvfs.listdir(path)
    for _dir in dirs:
        rmtree(os.path.join(path, _dir))
    for _file in files:
        xbmcvfs.delete(os.path.join(path, _file))
    xbmcvfs.rmdir(path)


def cleanup_temp_dir():
    try:
        rmtree(TEMP)
    except:
        pass

    xbmcvfs.mkdirs(TEMP)


def download_url_content_to_temp(url, filename):
    """
    Write the URL contents to a temp file.
    """
    temp_file = os.path.join(TEMP, filename)
    logger.info("Downloading URL {} to {}".format(url, temp_file))

    local_file_handle = xbmcvfs.File(temp_file, "wb")
    local_file_handle.write(urlopen(url).read())
    local_file_handle.close()

    return temp_file
