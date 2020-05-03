# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from codequick import Listitem, Script
import inputstreamhelper
from .contants import url_constructor, ROOT_CONFIG, IMG_PUBLIC, TVSHOW, CHANNEL, CHANNEL_CAT, MOVIE, MUSIC, EPISODE, _STAR_CHANNELS, IMG_THUMB_H_URL, IMG_POSTER_V_URL, IMG_FANART_H_URL, MEDIA_TYPE
from .api import deep_get, JioAPI
from urllib import urlencode


class Builder:

    def __init__(self, refs):
        self.callbackRefs = {}
        for r in refs:
            self.callbackRefs[r.__name__] = r

    def buildMenu(self):
        for name, id in ROOT_CONFIG:
            yield Listitem.from_dict(**{
                "label": name,
                "callback": self.callbackRefs.get("menu_list"),
                "params": {"url": url_constructor("/apis/2ccce09e59153fc9/v1/plus-home/getget/%s/0" % id)}
            })

    def buildSearch(self, callback):
        return Listitem().search(**{
            "callback": self.callbackRefs.get("tray_list"),
        })

    def buildPage(self, data, nextPageUrl=None):
        for each in data:
            if each.get("channelType") == "apps":
                continue
            art = info = None
            aItems = each.get("items")
            if aItems:
                info = {
                    "plot": "Contains : " + " | ".join([x.get("showname") or x.get("name") or "" for x in aItems])
                }
                art = self._getART(aItems[0])
            yield Listitem().from_dict(**{
                "label": each.get("title"),
                "art": art,
                "info": info,
                "callback": self.callbackRefs.get("tray_list"),
                "properties": {
                    "IsPlayable": False
                },
                "params": {
                    "url": url_constructor("/apis/common/v2/conflist/get/b379a65adea03173/%s" % each.get("id")),
                }
            })
        if nextPageUrl:
            yield Listitem().next_page(url=nextPageUrl)

    def buildTray(self, items, nextPageUrl=None):
        for eachItem in items:
            yield Listitem().from_dict(**self._buildItem(eachItem))
        if nextPageUrl:
            yield Listitem().next_page(url=nextPageUrl)

    def _getART(self, item):
        iType = deep_get(item, "app.type")
        if iType in [17, 16, 19]:
            thumb = icon = poster = item.get(
                "tvImg") and IMG_PUBLIC + item.get("tvImg").replace("medium", "high")
            fanart = banner = item.get("promoImg") and IMG_PUBLIC + \
                item.get("promoImg").replace("medium", "high")
        else:
            thumb = icon = poster = item.get("image") and IMG_PUBLIC + \
                item.get("image").replace("medium", "high")
            fanart = banner = (item.get("tvStill") and IMG_PUBLIC + item.get("tvStill")) or (
                item.get("tvBanner") and IMG_PUBLIC + item.get("tvBanner"))
        return {
            "thumb": thumb,
            "icon": icon,
            "poster": poster,
            "fanart": fanart,
            "banner": banner
        }

    def buildPlay(self, data, label=""):

        if data.get("vendor") == "hotstar":
            return Listitem().from_dict(**{
                "label": label,
                "callback": data.get("playbackUrl"),
                "properties": {
                    "IsPlayable": True,
                    "inputstreamaddon": "inputstream.adaptive",
                    "inputstream.adaptive.stream_headers": urlencode(data.get("headers", {})),
                    "inputstream.adaptive.manifest_type": data.get("playbackProto"),
                }
            })
        elif data.get("vendor") == "Sony Pictures":
            if data.get("licenceUrl"):
                is_helper = inputstreamhelper.Helper(
                    "mpd", drm="com.widevine.alpha")
                if is_helper.check_inputstream():
                    Script.log("licenceUrl %s" %
                               data.get("licenceUrl"), lvl=Script.INFO)
                    return Listitem().from_dict(**{
                        "label": label,
                        "callback": data.get("playbackUrl"),
                        "properties": {
                            "IsPlayable": True,
                            "inputstreamaddon": is_helper.inputstream_addon,
                            "inputstream.adaptive.manifest_type": data.get("playbackProto"),
                            "inputstream.adaptive.license_type": "com.widevine.alpha",
                            "inputstream.adaptive.license_key": data.get("licenceUrl") + "||R{SSM}|",
                        }
                    })
            return Listitem().from_dict(**{
                "label": label,
                "callback": data.get("playbackUrl"),
                "properties": {
                    "IsPlayable": True,
                    "inputstreamaddon": "inputstream.adaptive",
                    "inputstream.adaptive.manifest_type": data.get("playbackProto"),
                }
            })
        else:
            Script.log("licenceUrl %s" %
                       data.get("licenceUrl"), lvl=Script.INFO)
            is_helper = inputstreamhelper.Helper(
                "mpd", drm="com.widevine.alpha")
            if is_helper.check_inputstream():
                return Listitem().from_dict(**{
                    "label": label,
                    "callback": data.get("playbackUrl"),
                    "subtitles": data.get("subtitles"),
                    "properties": {
                        "IsPlayable": True,
                        "inputstreamaddon": is_helper.inputstream_addon,
                        "inputstream.adaptive.stream_headers": urlencode(data.get("headers", {})),
                        "inputstream.adaptive.manifest_type": data.get("playbackProto"),
                        "inputstream.adaptive.license_type": "com.widevine.alpha",
                        "inputstream.adaptive.license_key": data.get("licenseUrl"),
                    }
                })
        return False

    def buildPlayFromURL(self, playbackUrl, licenceUrl=None, label="", headers={}):
        return Listitem().from_dict(**{
            "label": label,
            "callback": playbackUrl,
            "properties": {
                "IsPlayable": True,
                "inputstreamaddon": "inputstream.adaptive",
                "inputstream.adaptive.stream_headers": urlencode(headers),
                "inputstream.adaptive.manifest_type": "hls",
            }
        })

    def buildLive(self, label, playbackUrl, licenseUrl, headers={}):
        headers = urlencode(headers)
        is_helper = inputstreamhelper.Helper("mpd", drm="com.widevine.alpha")
        if is_helper.check_inputstream():
            return Listitem().from_dict(**{
                "label": label,
                "callback": playbackUrl,
                "properties": {
                    "IsPlayable": True,
                    "inputstreamaddon": is_helper.inputstream_addon,
                    "inputstream.adaptive.stream_headers": headers,
                    "inputstream.adaptive.manifest_type": "mpd",
                    "inputstream.adaptive.license_type": "com.widevine.alpha",
                    "inputstream.adaptive.license_key": licenseUrl + "|%s|R{SSM}|" % (headers),
                }
            })

    def _buildItem(self, item):
        itype = deep_get(item, "app.type")
        # For label
        if item.get("episodes"):
            if item.get("season"):
                label = "Season %s (%s)" % (
                    item.get("season"), len(item.get("episodes")))
            else:
                label = datetime(int(item.get("year", "2020")), int(
                    item.get("month", "03")), 1).strftime("%B %Y")
        elif item.get("episodeNo"):
            label = item.get("subtitle") or item.get("name")
        else:
            label = item.get("name")

        # For list
        if item.get("episodeNo"):
            callback = self.callbackRefs.get("play_vod")
            Script.log("Playing %s" % (item.get("id")
                                       or item.get("contentId", "No id found")), lvl=Script.INFO)
            Script.log("Got vendor %s " % item.get("vendor"), lvl=Script.INFO)
            params = {
                "Id": item.get("id") or item.get("contentId"),
                "label": label,
                "extId": item.get("deepLinkUrl") and item.get("deepLinkUrl").split("/")[-1],
                "vendor": item.get("vendor")
            }
        elif item.get("episodes"):
            if item.get("season"):
                url = url_constructor(
                    "/apis/2ccce09e59153fc9/v1/plus-metamore/get/%s/%s" % (item.get("id"), item.get("season")))
            else:
                url = url_constructor(
                    "/apis/2ccce09e59153fc9/v1/plus-metamore/get/%s/%s/%s" % (item.get("id"), item.get("year"), item.get("month")))
            params = {"url": url}
            callback = self.callbackRefs.get("tray_list")
        elif itype == TVSHOW:
            params = {"url": url_constructor(
                "/apis/2ccce09e59153fc9/v1/plus-metamore/get/%s" % item.get("id"))}
            callback = self.callbackRefs.get("tray_list")
        # elif itype == CHANNEL_CAT:
        #     pass
        elif itype == CHANNEL:
            if item.get("provider") == "SonyLIV":
                callback = self.callbackRefs.get("play_vod")
                params = {
                    "Id": item.get("id") or item.get("contentId"),
                    "label": label,
                    "extId": item.get("deepLinkUrl") and item.get("deepLinkUrl").split("/")[-1],
                    "vendor": "Sony Pictures"
                }
            elif item.get("provider") == "Hotstar":
                cname = _STAR_CHANNELS.get(
                    int(item.get("jiotvId") or item.get("id")))
                hotauth = JioAPI.getStarAuth()
                if item.get("jiotvId") in [160, 362, 460, 461, 159]:
                    callback = self.callbackRefs.get("play_live")
                    licenseUrl = "https://ipl.service.expressplay.com/hms/wv/rights/?ExpressPlayToken=BQAAABNlKfMAAAAAAGB5RXIUhuAKhb0o_gG4s6_qdxw4y5xQZyNGjvsbfiltjdLAStqy3hyJnAzQPRNmTknPc1nMTsezyHAxVCdu2VYmI-bCaJTYMefMpfs-fql1lF_B7Zrj-qyxdlafY1xKq42c6z1i9s1FPsE_z8wV6FC8BHNpMw&req_id=2f652cd6"
                    stype = "mpd"
                    headers = {"User-Agent": "hotstar",
                               "Content-Type": "application/octet-stream"}
                else:
                    callback = self.callbackRefs.get("play_url")
                    licenseUrl = None
                    stype = "m3u8"
                    headers = {"User-Agent": "hotstar"}
                params = {
                    "playbackUrl": "http://hotstar.live.cdn.jio.com/hotstar_isl/%s/master.%s?hdnea=%s" % (cname, stype, hotauth),
                    "licenseUrl": licenseUrl,
                    "label": label,
                    "headers": {"User-Agent": "hotstar"}
                }
            else:
                callback = self.callbackRefs.get("play_live")
                playbackUrl, licenseUrl = JioAPI.getLiveUrl(item.get("id"))
                params = {
                    "label": label,
                    "playbackUrl": playbackUrl,
                    "licenseUrl": licenseUrl,
                    "headers": JioAPI._getLiveHeaders()
                }
        elif itype == MUSIC:
            callback = self.callbackRefs.get("play_url")
            params = {
                # + "?" + JioAPI.getTokenParams(),
                "playbackUrl": item.get("tvurl") and item.get("tvurl").replace("jiovod.cdn.jio.com", "jiovod.wdrm.cdn.jio.com").replace("smil:vod", "smil:vodpublic"),
                "licenceUrl": None,
                "label": label,
                "headers": JioAPI._getPlayHeaders()[0]
            }
        else:
            callback = self.callbackRefs.get("play_vod")
            params = {
                "Id": item.get("id") or item.get("contentId"),
                "label": label,
                "extId": item.get("extId"),
                "vendor": item.get("vendor")
            }

        return {
            "label": label,
            "art": self._getART(item),
            "info": {
                "genre": item.get("genres"),
                "episode": item.get("episodeNo"),
                # "season": item.get("season"),
                "mpaa": item.get("maturityRating"),
                "plot": item.get("description") or item.get("desc"),
                "title": item.get("name"),
                "sorttitle": item.get("subtitle"),
                "duration": item.get("totalDuration"),
                "cast": item.get("artist") or item.get("starcast"),
                "director": item.get("directors"),
                "studio": item.get("vendor"),
                "premiered": item.get("uploadedDate") and item.get("uploadedDate")[:10],
                "tag": item.get("tags"),
                "path": "",
                "trailer": "",
                "dateadded": item.get("uploadedDate") and item.get("uploadedDate")[:10],
                "mediatype": MEDIA_TYPE.get(item.get("type"))
            },
            "properties": {
                "IsPlayable": False
            },
            "callback": callback,
            "params": params
        }
