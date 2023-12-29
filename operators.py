import json
from typing import Set
from bpy.types import Context
import requests
import bpy

from .connect_to_spotify import *

accessToken = "foo"


headers = {
    "Authorization": f"Bearer {accessToken}"
}



def getPlaybackData(wm):
        playbackData = requests.get('https://api.spotify.com/v1/me/player', headers=headers)
        playbackJson = playbackData.json()
        
        wm['songName'] = f"{playbackJson['item']['name']} - {playbackJson['item']['artists'][0]['name']}"
        
def getPlaylistData(wm):
        wm.playlists.clear()
        playlistData = requests.get(
            'https://api.spotify.com/v1/me/playlists?limit=5&offset=0', headers=headers)
        playlists = playlistData.json()['items']
        for playlist in playlists:
            container = wm.playlists.add()
            container.name = playlist['name']
            container.uri = f"spotify:playlist:{playlist['id']}"

def getAlbumData(wm):
    wm.albums.clear()
    params = {
        'limit': '5',
        'offset': '0'
    }
    albumData = requests.get(
        'https://api.spotify.com/v1/me/albums', headers=headers, params=params
    )
    items = albumData.json()['items']
    for item in items:
        album = item['album']
        container = wm.albums.add()
        container.name = album['name']
        container.uri = f"spotify:album:{album['id']}"

def getArtistData(wm):
    wm.artists.clear()
    params = {
        'type': 'artist',
        'limit': '5'
    }
    albumData = requests.get(
        'https://api.spotify.com/v1/me/following', headers=headers, params=params
    )
    
    print(albumData.json())
    
    items = albumData.json()['artists']['items']
    for item in items:
        container = wm.artists.add()
        container.name = item['name']
        container.uri = f"spotify:artist:{item['id']}"

class RefreshSpotify(bpy.types.Operator):
    """Refresh Spotify playback info"""
    bl_idname = "spotify.refresh"
    bl_label = "Refresh"
    bl_context = "VIEW_3D"

    def execute(self, context):
        wm = bpy.context.window_manager

        getPlaybackData(wm)
        getPlaylistData(wm)
        getAlbumData(wm)
        getArtistData(wm)

        return {'FINISHED'}
    
def RefreshBlah():
    RefreshSpotify.execute(None, bpy.context)

class SkipSpotify(bpy.types.Operator):
    """Skip to the next song"""
    bl_idname = "spotify.skip"
    bl_label = ""
    bl_context = "VIEW_3D"

    def execute(self, context):
        print(requests.post('https://api.spotify.com/v1/me/player/next', headers=headers).json)
        bpy.app.timers.register(RefreshBlah, first_interval=0.5)
        RefreshSpotify.execute(None, bpy.context)
        
        return {'FINISHED'}

class RewindSpotify(bpy.types.Operator):
    """Rewind to the previous song"""
    bl_idname = "spotify.rewind"
    bl_label = ""
    bl_context = "VIEW_3D"

    def execute(self, context):
        print(requests.post('https://api.spotify.com/v1/me/player/previous', headers=headers).json)
        bpy.app.timers.register(RefreshBlah, first_interval=0.5)
        
        return {'FINISHED'}
    
class PauseSpotify(bpy.types.Operator):
    """Pause the song"""
    bl_idname = "spotify.pause"
    bl_label = ""
    bl_context = "VIEW_3D"

    def execute(self, context):
        print(requests.put('https://api.spotify.com/v1/me/player/pause', headers=headers).json)
        bpy.app.timers.register(RefreshBlah, first_interval=0.5)
        
        return {'FINISHED'}
    
class PlaySpotify(bpy.types.Operator):
    """Play the song / playlist"""    
    bl_idname = "spotify.playplaylist"
    bl_label = ""
    bl_context = "VIEW_3D"
    
    uri: bpy.props.StringProperty(name = "uri")
    
    def execute(self, context):
        body = {
            "context_uri": self.uri
        }
        if (self.uri):
            requests.put(
                r'https://api.spotify.com/v1/me/player/play', 
                headers=headers, data=json.dumps(body))
        else:
            requests.put(r'https://api.spotify.com/v1/me/player/play', headers=headers)
        
        bpy.app.timers.register(RefreshBlah, first_interval=0.5)
        
        return {'FINISHED'}