import os
import bpy

# Credit to Machin3io for these functions


# get the folder path for the .py file containing this function
def get_path():
    return os.path.dirname(os.path.realpath(__file__))


# get the name of the "base" folder
def get_name():
    return os.path.basename(get_path())


# now that we have the addons name we can get the preferences
def get_prefs():
    return bpy.context.preferences.addons[get_name()].preferences
