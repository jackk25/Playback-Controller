bl_info = {
        "name": "Spotify Controller",
        "author": "jackk25",
        "version": (1, 0, 0),
        "blender": (4, 0, 0),
        "category": "3D View",
        "location": "3D View > Sidebar > Spotify",
        "description": "Control Spotify playback from inside Blender."
}

# Allows reloading through F8, "Reload Script", etc. without breaking
if "bpy" in locals():
    import importlib
    if "operators" in locals():
        importlib.reload(operators)
    if "ui_panels" in locals():
        importlib.reload(ui_panels)

import bpy
from .operators import *
from .ui_panels import *
from .connect_to_spotify import *

class PromptUser(bpy.types.Operator):
    bl_idname = "spotify.prompt"
    bl_label = "Step 1: Click Me"
    bl_context = "VIEW_3D"

    def execute(self, context):
        promptUserForAuth("user-modify-playback-state user-read-playback-state playlist-read-private user-library-read user-follow-read")
        
        return {'FINISHED'}

class AuthenticateUser(bpy.types.Operator):
    bl_idname = "spotify.auth"
    bl_label = "Step 2: Put URL Above, Then Click Me"
    bl_context = "VIEW_3D"

    @classmethod
    def poll(cls, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        return addon_prefs.authUrl != ''

    def execute(self, context):
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        authToken, refreshToken = authenticateUser(
            url=addon_prefs.authUrl, state=addon_prefs.state, codeVerifier=addon_prefs.state
        )

        addon_prefs.authUrl = ''
        addon_prefs.state = ''
        addon_prefs.code_verifier = ''

        addon_prefs.refreshToken = refreshToken
        
        return {'FINISHED'}


class AddonPreferences(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    delay: bpy.props.FloatProperty(
        name="Refresh Delay",
        description="Amount of time to wait before refreshing",
        subtype='TIME_ABSOLUTE',
        default=0.5
    )
    
    limit: bpy.props.IntProperty(
        name="List Limit",
        default=5,
    )

    authUrl: bpy.props.StringProperty(
        name="Auth URL (DO NOT SHARE!!!!!!!)",
        description="Your url to auth with Spotify servers (DO NOT SHARE THIS, SEND THIS, ETC)",
        subtype='PASSWORD'
    )


    refreshToken: bpy.props.StringProperty(
        name="Refresh Token (DO NOT SHARE!!!!!!!)",
        description="Your token to Spotify servers (DO NOT SHARE THIS, SEND THIS, ETC)",
        subtype='PASSWORD'
    )

    codeVerifier: bpy.props.StringProperty(
        name="Code Verifier (DO NOT SHARE!!!!!!!)",
        description="Your code verifier for authentication to Spotify servers (DO NOT SHARE THIS, SEND THIS, ETC)",
        subtype='PASSWORD'
    )

    state: bpy.props.StringProperty(
        name="State (DO NOT SHARE!!!!!!!)",
        description="Your state for authentication (DO NOT SHARE THIS, SEND THIS, ETC)",
        subtype='PASSWORD'
    )


    def draw(self, context):
        layout = self.layout
        
        if self.refreshToken == '':
            row = layout.row()
            row.operator(PromptUser.bl_idname)
            row.prop(self, "authUrl")
            row.operator(AuthenticateUser.bl_idname)
        
        layout.prop(self, "delay")
        layout.prop(self, "limit")
        layout.prop(self, "refreshToken")

    
classes = [
    AddonPreferences,
    PromptUser,
    AuthenticateUser,
    SPOTIFY_PT_Player, 
    SPOTIFY_PT_Playlists, 
    SPOTIFY_PT_Albums,
    SPOTIFY_PT_Artists,
    RefreshSpotify, 
    SkipSpotify, 
    RewindSpotify, 
    PauseSpotify, 
    TrackContainer, 
    PlaySpotify,
]    

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.WindowManager.songName = bpy.props.StringProperty(name="songName")
    bpy.types.WindowManager.playlists = bpy.props.CollectionProperty(type=TrackContainer)
    bpy.types.WindowManager.albums = bpy.props.CollectionProperty(type=TrackContainer)
    bpy.types.WindowManager.artists = bpy.props.CollectionProperty(type=TrackContainer)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        
    del bpy.types.WindowManager.songName
    del bpy.types.WindowManager.playlists
    del bpy.types.WindowManager.albums
    del bpy.types.WindowManager.artists

if __name__ == "__main__":
    register()

    