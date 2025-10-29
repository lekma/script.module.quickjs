# -*- coding: utf-8 -*-


import json
import os
import pathlib
import platform
import stat
import subprocess
import sys
import urllib
import zipfile

import xbmc, xbmcaddon, xbmcgui, xbmcvfs

from packaging.version import Version


# ------------------------------------------------------------------------------
# QuickJSInstaller

class QuickJSInstaller(object):

    __addon_id__ = "script.module.quickjs"
    __addon__ = xbmcaddon.Addon(__addon_id__)

    __kodi_path__ = "special://home/system/quickjs/qjs"
    __path__ = pathlib.Path(xbmcvfs.translatePath(__kodi_path__))
    __url__ = urllib.parse.urlparse(
        "https://bellard.org/quickjs/binary_releases"
    )

    __progress__ = xbmcgui.DialogProgress()
    __mode__ = (stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)

    __current_version__ = None
    __latest_version__ = None
    __confirmed__ = None

    @classmethod
    def __log__(cls, msg, level=xbmc.LOGINFO):
        xbmc.log(f"[{cls.__addon_id__}] {msg}", level=level)

    @classmethod
    def __string__(cls, _id_):
        return cls.__addon__.getLocalizedString(_id_)

    @classmethod
    def __installed__(cls):
        return (cls.__path__.is_file() and os.access(cls.__path__, os.X_OK))

    @classmethod
    def __run__(cls, *args, check=True):
        return subprocess.run(
            args, check=check, stdout=subprocess.PIPE, text=True
        ).stdout.strip()

    @classmethod
    def __confirm__(cls):
        if cls.__confirmed__ is None:
            cls.__confirmed__ = xbmcgui.Dialog().yesno(
                cls.__string__(30000),
                cls.__string__(30001).format(cls.__latest__())
            )
        return cls.__confirmed__

    @classmethod
    def __current__(cls):
        if not cls.__current_version__:
            cls.__current_version__ =  cls.__run__(
                f"{cls.__path__}", "-h", check=False
            ).splitlines()[0].split(" ")[-1]
        return cls.__current_version__

    @classmethod
    def __latest__(cls):
        if not cls.__latest_version__:
            with urllib.request.urlopen(
                cls.__url__._replace(
                    path=f"{cls.__url__.path}/LATEST.json"
                ).geturl()
            ) as response:
                cls.__latest_version__ = json.loads(
                    response.read().decode("utf-8").strip()
                )["version"]
        return cls.__latest_version__

    @classmethod
    def __target__(cls):
        return f"quickjs-{sys.platform}-{platform.machine()}"

    @classmethod
    def __update__(cls, block_count, block_size, total_size):
        cls.__progress__.update(
            ((block_count * block_size) * 100) // total_size
        )

    @classmethod
    def __install__(cls):
        url = cls.__url__._replace(
            path=f"{cls.__url__.path}/{cls.__target__()}-{cls.__latest__()}.zip"
        ).geturl()
        cls.__progress__.create(
            cls.__string__(30000),
            cls.__string__(30002).format(cls.__latest__())
        )
        path, _ = urllib.request.urlretrieve(url, reporthook=cls.__update__)
        cls.__progress__.close()
        os.makedirs(cls.__path__.parent, exist_ok=True)
        with zipfile.ZipFile(path, "r") as zip_file:
            zip_file.extract("qjs", path=cls.__path__.parent)
        pathlib.Path(path).unlink()
        cls.__path__.chmod(cls.__mode__)
        cls.__current_version__ = None
        xbmcgui.Dialog().ok(
            cls.__string__(30000),
            cls.__string__(30004).format(cls.__latest__())
        )

    # --------------------------------------------------------------------------

    def __init__(self):
        if (
            (
                (not self.__installed__()) or
                (
                    Version(self.__current__().replace("-", ".")) <
                    Version(self.__latest__().replace("-", "."))
                )
            ) and
            self.__confirm__()
        ):
            self.__install__()


# ------------------------------------------------------------------------------

def path():
    if ((installer := QuickJSInstaller()).__installed__()):
        return str(installer.__path__)

def version():
    if ((installer := QuickJSInstaller()).__installed__()):
        return str(installer.__current__())
