import json
import requests
import bpy
import queue
import time
from concurrent.futures import ThreadPoolExecutor

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


def getPlaybackData(count, resultsDict):
    playbackData = requests.get(
        "https://api.spotify.com/v1/me/player", headers=getHeader()
    )
    if playbackData.status_code == 204:
        # Playback has not started yet
        songName = ""
        artistString = ""
        shuffleStatus = False
        repeatStatus = "off"

        resultsDict["songName"] = songName
        resultsDict["artistString"] = artistString
        resultsDict["shuffleStatus"] = shuffleStatus
        resultsDict["repeatStatus"] = repeatStatus
        return

    elif playbackData.status_code == 401:
        # Don't want to spam the server if it won't work
        # This could be a pref
        if count <= 2:
            refreshAndUpdate(count, resultsDict)
            getPlaybackData(count + 1)
    elif count > 2:
        return

    playbackJson = playbackData.json()

    songName = playbackJson["item"]["name"]
    artistString = ""
    for artist in playbackJson["item"]["artists"]:
        artistString += f"{artist['name']}"

    shuffleStatus = playbackJson["shuffle_state"]
    repeatStatus = playbackJson["repeat_state"]

    resultsDict["songName"] = songName
    resultsDict["artistString"] = artistString
    resultsDict["shuffleStatus"] = shuffleStatus
    resultsDict["repeatStatus"] = repeatStatus

    print(resultsDict)


def addToTrackContainers(wm, containerJson):
    container = wm.containers.add()
    container.name = containerJson["name"]
    container.containerId = containerJson["id"]
    container.containerType = containerJson["type"]
    container.href = containerJson["href"]


def getPlaylistData(count: int, queue: queue.Queue):
    startTime = time.time()
    print("Getting Playlist Data")
    params = {"limit": str(listLimit), "offset": "0"}
    playlistData = requests.get(
        "https://api.spotify.com/v1/me/playlists", headers=getHeader(), params=params
    )

    if playlistData.status_code == 401:
        if count <= 2:
            refreshAndUpdate()
            getPlaylistData(count + 1, queue)
        else:
            return

    playlists = playlistData.json()["items"]

    for playlist in playlists:
        queue.put(playlist)

    endTime = time.time()
    print(f"Playlist Data Time: {endTime - startTime}")


def getAlbumData(count: int, queue: queue.Queue):
    startTime = time.time()
    print("Getting Album Data")
    params = {"limit": str(listLimit), "offset": "0"}
    albumData = requests.get(
        "https://api.spotify.com/v1/me/albums", headers=getHeader(), params=params
    )

    if albumData.status_code == 401:
        if count <= 2:
            refreshAndUpdate()
            getAlbumData(count + 1, queue)
        else:
            return

    items = albumData.json()["items"]

    for item in items:
        # Why are albums like this :(
        album = item["album"]
        queue.put(album)

    endTime = time.time()
    print(f"Album Data Time: {endTime - startTime}")


def getArtistData(count: int, queue: queue.Queue):
    startTime = time.time()
    print("Getting Artist Data")
    params = {"type": "artist", "limit": str(listLimit)}
    artistData = requests.get(
        "https://api.spotify.com/v1/me/following", headers=getHeader(), params=params
    )

    if artistData.status_code == 401:
        if count <= 2:
            refreshAndUpdate()
            getArtistData(count + 1, queue)
        else:
            return

    arists = artistData.json()["artists"]["items"]

    for artist in arists:
        queue.put(artist)

    endTime = time.time()

    print(f"Artist Data Time: {endTime-startTime}")


class RefreshSpotify(bpy.types.Operator):
    """Refresh Spotify playback info"""

    bl_idname = "spotify.refresh"
    bl_label = "Refresh"
    bl_context = "VIEW_3D"

    fullRefresh: bpy.props.BoolProperty("fullRefresh", default=False)

    def execute(self, context):
        wm = bpy.context.window_manager

        fullStartTime = time.time()
        results = {}
        with ThreadPoolExecutor() as executor:
            playbackFuture = executor.submit(getPlaybackData, 0, results)

            if self.fullRefresh == True:
                containerQueue = queue.Queue(maxsize=0)
                wm.containers.clear()

                playlistFuture = executor.submit(getPlaylistData, 0, containerQueue)
                albumFuture = executor.submit(getAlbumData, 0, containerQueue)
                artistFuture = executor.submit(getArtistData, 0, containerQueue)

                playlistFuture.result()
                albumFuture.result()
                artistFuture.result()

                containerQueue.put(None)

                uiTime = time.time()

                for container in iter(containerQueue.get, None):
                    addToTrackContainers(wm, container)

                endTime = time.time()
                print(f"Time to update UI: {endTime-uiTime}")

            endTime = time.time()
            playbackFuture.result()
            songName = results["songName"]
            artistString = results["artistString"]
            wm.songName = f"{songName} - {artistString}"
            print(f"Full execution time: {endTime-fullStartTime}")

        return {"FINISHED"}


def PartialRefresh():
    bpy.ops.spotify.refresh("EXEC_DEFAULT")


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

    bl_idname = "spotify.play_playlist"
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


class ShuffleSpotify(bpy.types.Operator):
    """Toggle the shuffle on / off"""

    bl_idname = "spotify.shuffle"
    bl_label = ""
    bl_context = "VIEW_3D"

    def execute(self, context):
        return {"FINISHED"}


class LoopSpotify(bpy.types.Operator):
    """Change the loop mode"""

    bl_idname = "spotify.change_loop"
    bl_label = ""
    bl_context = "VIEW_3D"

    def execute(self, context):
        return {"FINISHED"}
