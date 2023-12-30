import json
import requests
import bpy
import threading

from .connect_to_spotify import *

def getHeader():
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons["Playback-Controller"].preferences

    accessToken = addon_prefs.authToken

    headers = {"Authorization": f"Bearer {accessToken}"}

    return headers

listLimit = 5

def refreshAndUpdate():
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons["Playback-Controller"].preferences

    refreshToken = addon_prefs.refreshToken

    authToken, refreshToken = refreshAuthorization(refreshToken)

    addon_prefs.authToken = authToken
    addon_prefs.refreshToken = refreshToken

def getPlaybackData(wm, count):
    playbackData = requests.get(
        "https://api.spotify.com/v1/me/player", headers=getHeader()
    )
    if playbackData.status_code == 204:
        #Playback has not started yet
        songName = ""
        artistString = ""
        shuffleStatus = False
        repeatStatus = "off"

        wm.songName = ""

        return
    elif playbackData.status_code == 401:
        # Don't want to spam the server if it won't work
        # This could be a pref
        if count <= 2:
            refreshAndUpdate()
            getPlaybackData(wm, count)
    elif count > 2:
        return

    playbackJson = playbackData.json()

    songName = playbackJson["item"]["name"]
    artistString = ""
    for artist in playbackJson["item"]["artists"]:
        artistString += f"{artist['name']}"

    shuffleStatus = playbackJson["shuffle_state"]
    repeatStatus = playbackJson["repeat_state"]

    # Move this to it's own update function, away from the request and data collection
    wm["songName"] = f"{songName} - {artistString}"


def addToTrackContainers(wm, containerJson):
    container = wm.containers.add()
    container.name = containerJson["name"]
    container.containerId = containerJson["id"]
    container.containerType = containerJson["type"]
    container.href = containerJson["href"]

def getPlaylistData(wm, count):
    params = {"limit": str(listLimit), "offset": "0"}
    playlistData = requests.get(
        "https://api.spotify.com/v1/me/playlists", headers=getHeader(), params=params
    )

    if playlistData.status_code == 401:
        if count <= 2:
            refreshAndUpdate()
            getPlaylistData(wm, count)
        else:
            return

    playlists = playlistData.json()["items"]

    # Move this to it's own update function, away from the request and data collection
    for playlist in playlists:
        addToTrackContainers(wm, playlist)


def getAlbumData(wm, count):
    params = {"limit": str(listLimit), "offset": "0"}
    albumData = requests.get(
        "https://api.spotify.com/v1/me/albums", headers=getHeader(), params=params
    )

    if albumData.status_code == 401:
        if count <= 2:
            refreshAndUpdate()
            getAlbumData(wm, count)
        else:
            return

    items = albumData.json()["items"]

    # Move this to it's own update function, away from the request and data collection
    for item in items:
        # Why are albums like this :(
        album = item["album"]
        addToTrackContainers(wm, album)


def getArtistData(wm, count):
    params = {"type": "artist", "limit": str(listLimit)}
    artistData = requests.get(
        "https://api.spotify.com/v1/me/following", headers=getHeader(), params=params
    )
    
    if artistData.status_code == 401:
        if count <= 2:
            refreshAndUpdate()
            getArtistData(wm, count)
        else:
            return

    arists = artistData.json()["artists"]["items"]

    # Move this to it's own update function, away from the request and data collection
    for artist in arists:
        addToTrackContainers(wm, artist)


class RefreshSpotify(bpy.types.Operator):
    """Refresh Spotify playback info"""

    bl_idname = "spotify.refresh"
    bl_label = "Refresh"
    bl_context = "VIEW_3D"

    fullRefresh: bpy.props.BoolProperty("fullRefresh", default=False)

    def execute(self, context):
        wm = bpy.context.window_manager
        
        # Add threading to me!!!

        getPlaybackData(wm, 0)

        if self.fullRefresh == True:
            wm.containers.clear()
            print(self.fullRefresh)
            getPlaylistData(wm, 0)
            getAlbumData(wm, 0)
            getArtistData(wm, 0)

        return {"FINISHED"}


def PartialRefresh():
    bpy.ops.spotify.RefreshSpotify('EXEC_DEFAULT')

class SkipSpotify(bpy.types.Operator):
    """Skip to the next song"""

    bl_idname = "spotify.skip"
    bl_label = ""
    bl_context = "VIEW_3D"

    def execute(self, context):
        print(
            requests.post(
                "https://api.spotify.com/v1/me/player/next", headers=getHeader()
            ).json
        )

        bpy.app.timers.register(PartialRefresh, first_interval=0.5)

        return {"FINISHED"}


class RewindSpotify(bpy.types.Operator):
    """Rewind to the previous song"""

    bl_idname = "spotify.rewind"
    bl_label = ""
    bl_context = "VIEW_3D"

    def execute(self, context):
        print(
            requests.post(
                "https://api.spotify.com/v1/me/player/previous", headers=getHeader()
            ).json
        )
        bpy.app.timers.register(PartialRefresh, first_interval=0.5)

        return {"FINISHED"}


class PauseSpotify(bpy.types.Operator):
    """Pause the song"""

    bl_idname = "spotify.pause"
    bl_label = ""
    bl_context = "VIEW_3D"

    def execute(self, context):
        print(
            requests.put(
                "https://api.spotify.com/v1/me/player/pause", headers=getHeader()
            ).json
        )
        bpy.app.timers.register(PartialRefresh, first_interval=0.5)

        return {"FINISHED"}


class PlaySpotify(bpy.types.Operator):
    """Play the song / playlist"""

    bl_idname = "spotify.playplaylist"
    bl_label = ""
    bl_context = "VIEW_3D"

    uri: bpy.props.StringProperty(name="uri")

    def execute(self, context):
        body = {"context_uri": self.uri}
        if self.uri:
            requests.put(
                r"https://api.spotify.com/v1/me/player/play",
                headers=getHeader(),
                data=json.dumps(body),
            )
        else:
            requests.put(
                r"https://api.spotify.com/v1/me/player/play", headers=getHeader()
            )

        bpy.app.timers.register(PartialRefresh, first_interval=0.5)

        return {"FINISHED"}
