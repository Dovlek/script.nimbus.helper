# -*- coding: utf-8 -*-
from urllib.parse import quote
from xbmc import executebuiltin, getInfoLabel

# from modules.logger import logger


def person_search(params):
    return executebuiltin(
        "RunPlugin(plugin://plugin.video.fen/?mode=person_search_choice&query=%s)"
        % params["query"]
    )


def actor_search_seren(params):
    query = getInfoLabel("Skin.String(nimbus.actor.query)")
    media_type = getInfoLabel("Skin.String(nimbus.actor.type)")
    if not query:
        return
    action = "movieByActor" if media_type == "movie" else "showsByActor"
    url = f"plugin://plugin.video.seren/?action={action}&actionArgs={quote(query)}"
    executebuiltin(f'ActivateWindow(Videos,"{url}",return)')


def extras(params):
    return executebuiltin(
        "RunPlugin(%s)" % getInfoLabel("ListItem.Property(fen.extras_params)")
    )
