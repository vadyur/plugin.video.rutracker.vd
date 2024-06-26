# -*- coding: utf-8 -*-
import xbmc
import os, sys

__id_plugin__ = (
    sys.argv[0].replace("plugin://", "").replace("/", "")
    if sys.argv[0].replace("plugin://", "").replace("/", "")
    else __import__("xbmcaddon").Addon().getAddonInfo("id")
)
__plugin_name__ = xbmc.getInfoLabel("System.AddonTitle(%s)" % __id_plugin__)
__plugin_version__ = xbmc.getInfoLabel("System.AddonVersion(%s)" % __id_plugin__)


def _decode(s):
    try:
        return s.decode("utf8")
    except:
        return s


def _encode(s):
    try:
        return s.encode("utf8")
    except:
        return s


def message(title: str, msg: str, times=5000, icon=None):
    if icon is None:
        icon = xbmc.getInfoLabel("System.AddonIcon(%s)" % __id_plugin__)
    try:
        xbmc.executebuiltin(
            'XBMC.Notification("%s", "%s", %s, "%s")' % (title, msg, times, icon)
        )
    except Exception as e:
        xbmc.log("Message: " + str(e), xbmc.LOGERROR)


def log(e, msgerror=None, logger=None, msgwarning=True):
    # global pformat
    from pprint import pformat

    def _format_vars(variables):
        """
        Format variables dictionary

        :param variables: variables dict
        :type variables: dict
        :return: formatted string with sorted ``var = val`` pairs
        :rtype: str
        """
        var_list = [(var, val) for var, val in variables.items()]
        lines = []
        for var, val in sorted(var_list, key=lambda i: i[0]):
            if not (var.startswith("__") or var.endswith("__")):
                lines.append("{0} = {1}".format(var, pformat(val)))
        return "\n".join(lines)

    # def logger(s):
    # print(s)
    if isinstance(e, BaseException):
        # global uname, inspect, traceback
        from platform import uname  # type: ignore
        import inspect, traceback

        if logger is None:
            logger = lambda msg: xbmc.log(_decode(msg), xbmc.LOGERROR)
        frame_info = inspect.trace(5)[-1]
        logger("Unhandled exception detected!")
        logger("*** Start diagnostic info ***")
        logger("Plugin name: {0}".format(__plugin_name__))
        logger("Plugin version: {0}".format(__plugin_version__))
        logger("System info: {0}".format(uname()))
        logger(
            "OS info: {0}".format(
                xbmc.getInfoLabel("System.OSVersionInfo")
            )
        )
        logger("Kodi version: {0}".format(xbmc.getInfoLabel("System.BuildVersion")))
        logger("Python version: {0}".format(sys.version.replace("\n", "")))
        logger("File: {0}".format(frame_info[1]))
        context = ""
        if frame_info[4] is not None:
            for i, line in enumerate(frame_info[4], frame_info[2] - frame_info[5]): # type: ignore
                if i == frame_info[2]:
                    context += "{0}:>{1}".format(str(i).rjust(5), line)
                else:
                    context += "{0}: {1}".format(str(i).rjust(5), line)
        logger("Code context:\n" + context)
        logger("Global variables:\n" + _format_vars(frame_info[0].f_globals))
        logger("Local variables:\n" + _format_vars(frame_info[0].f_locals))
        logger("**** End diagnostic info ****")
        if msgerror:
            logger("**** Start traceback info ****")
            exc_type, exc_val, exc_tb = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_val, exc_tb, limit=30)
            logger(str(e))
            context = ""
            for line in lines:
                context += "{0}".format(line)
            logger(context)
            logger("**** End traceback info ****")
            logger(_decode(msgerror))
            if msgwarning:
                message(_decode(msgerror), str(e))
        else:
            raise
    else:
        if msgerror is None:
            msgerror = ""
        if logger:
            logger("{0}:{1} {2}".format(__plugin_name__, _decode(msgerror), _decode(e)))
        else:
            try:
                xbmc.log(
                    "{0}:{1} {2}".format(
                        __plugin_name__, _decode(msgerror), _decode(e)
                    )
                )
            except:
                xbmc.log(
                    "{0}:{1} {2}".format(
                        __plugin_name__, _decode(msgerror), pformat(e)
                    )
                )
