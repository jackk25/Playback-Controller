import bpy
from bpy.types import Panel, PropertyGroup, Menu
from bpy.props import StringProperty

from .operators import (
    RefreshSpotify,
    RewindSpotify,
    PauseSpotify,
    PlaySpotify,
    SkipSpotify,
)

class SpotfyPanel:
    bl_category = "Spotify"
    bl_space_type = 'VIEW_3D'
    bl_region_type = "UI"

class SPOTIFY_PT_Player(SpotfyPanel, Panel):
    bl_label = "Player"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        row = layout.row()
        row.label(text=wm["songName"])
        row.alignment = "CENTER"

        row = layout.row()
        row.operator(RewindSpotify.bl_idname, icon="TRACKING_BACKWARDS_SINGLE")
        row.operator(PauseSpotify.bl_idname, icon="PAUSE")
        row.operator(PlaySpotify.bl_idname, icon="PLAY")
        row.operator(SkipSpotify.bl_idname, icon="TRACKING_FORWARDS_SINGLE")
        row.alignment = "CENTER"

        row = layout.row(align=True)
        row.operator(RefreshSpotify.bl_idname, icon="FILE_REFRESH")


class TrackContainer(PropertyGroup):
    """Contains the name and URI of a 'track container', usually a playlist, album, or artist"""

    name: StringProperty(name="Name")
    containerId: StringProperty(name="ID")
    # This could be an enum property
    containerType: StringProperty(name="type")
    href: StringProperty(name="href")

def drawTrackContainerPanel(self, itemType):
    layout = self.layout

    for item in bpy.context.window_manager.containers:
        if item.containerType == itemType:
            row = layout.row()
            row.label(text=item.name)
            operator = row.operator(PlaySpotify.bl_idname, icon="PLAY")
            operator.uri = f"spotify:{item.containerType}:{item.uri}"

            #This shouldn't play a song, this should open a URL to the Spotify page of the thing!
            operator = row.operator('wm.url_open', icon="LINK_BLEND")
            operator.url = item.href

# Want to condense these all down even MORE
# Like with a base class and stuff
        
class SPOTIFY_PT_Playlists(SpotfyPanel, Panel):
    bl_label = "Playlists"

    def draw(self, context):
        drawTrackContainerPanel(self, "playlist")

class SPOTIFY_PT_Albums(SpotfyPanel, Panel):
    bl_label = "Albums"

    def draw(self, context):
        drawTrackContainerPanel(self, "album")


class SPOTIFY_PT_Artists(SpotfyPanel, Panel):
    bl_label = "Artists"

    def draw(self, context):
        drawTrackContainerPanel(self, "artist")


class AuthenticationMenu(Menu):
    bl_label = "Authentication Menu"
    bl_idname = "SPOTIFY_MT_authentication_menu"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="FEED ME URLS")
