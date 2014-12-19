# -*- coding: utf-8 -*-
import sys
import os
import random
import traceback
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs


__addon__ = xbmcaddon.Addon(id='screensaver.video')
__icon__ = __addon__.getAddonInfo('icon')
__cwd__ = __addon__.getAddonInfo('path').decode("utf-8")
__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources').encode("utf-8")).decode("utf-8")
__lib__ = xbmc.translatePath(os.path.join(__resource__, 'lib').encode("utf-8")).decode("utf-8")


sys.path.append(__lib__)

# Import the common settings
from settings import log
from settings import Settings
from settings import list_dir
from settings import os_path_join
from settings import dir_exists

from VideoParser import VideoParser


class ScreensaverWindow(xbmcgui.WindowXMLDialog):
    TIME_CONTROL = 3002

    # Static method to create the Window class
    @staticmethod
    def createScreensaverWindow():
        return ScreensaverWindow("screensaver-video-main.xml", __cwd__)

    # Called when setting up the window
    def onInit(self):
        xbmcgui.WindowXML.onInit(self)

        # Get the videos to use as a screensaver
        playlist = self._getPlaylist()
        # If there is nothing to play, then exit now
        if playlist is None:
            self.close()
            return

        # Update the playlist with any settings such as random start time
        self._updatePlaylistForSettings(playlist)

        # Now play the video
        xbmc.Player().play(playlist)

        # Set the video to loop, as we want it running as long as the screensaver
        xbmc.executebuiltin("PlayerControl(RepeatAll)")
        log("Started playing")

        # Now check to see if we are overlaying the time on the screen
        # Default is hidden
        timeControl = self.getControl(ScreensaverWindow.TIME_CONTROL)
        timeControl.setVisible(Settings.isShowTime())

        # Update any settings that need to be done after the video is playing
        self._updatePostPlayingForSettings(playlist)

    # Handle any activity on the screen, this will result in a call
    # to close the screensaver window
    def onAction(self, action):
        log("Action received: %s" % str(action.getId()))
        # For any action we want to close, as that means activity
        self.close()

    # The user clicked on a control
    def onClick(self, control):
        log("OnClick received")
        self.close()

    # A request to close the window has been made, tidy up the screensaver window
    def close(self):
        log("Ending Screensaver")
        # Exiting, so stop the video
        if xbmc.Player().isPlayingVideo():
            log("Stopping screensaver video")
            # There is a problem with using the normal "xbmc.Player().stop()" to stop
            # the video playing if another addon is selected - it will just continue
            # playing the video because the call to "xbmc.Player().stop()" will hang
            # instead we use the built in option
            xbmc.executebuiltin("PlayerControl(Stop)")

        # Reset the Player Repeat
        xbmc.executebuiltin("PlayerControl(RepeatOff)")

        log("Closing Window")
        xbmcgui.WindowXML.close(self)

    # Generates the playlist to use for the screensaver
    def _getPlaylist(self):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        # Check if we are showing all the videos in a given folder
        if Settings.isFolderSelection():
            videosFolder = Settings.getScreensaverFolder()
            if (videosFolder is None):
                videosFolder == ""

            # Check if we are dealing with a Folder of videos
            if videosFolder != "" and dir_exists(videosFolder):
                dirs, files = list_dir(videosFolder)
                # Now shuffle the playlist to ensure that if there are more
                #  than one video a different one starts each time
                random.shuffle(files)
                for vidFile in files:
                    fullPath = os_path_join(videosFolder, vidFile)
                    log("Screensaver video in directory is: %s" % fullPath)
                    playlist.add(fullPath)
        else:
            # Must be dealing with a single file
            videoFile = Settings.getScreensaverVideo()
            if (videoFile is None):
                videoFile == ""

            # Check to make sure the screensaver video file exists
            if (videoFile != "") and xbmcvfs.exists(videoFile):
                log("Screensaver video is: %s" % videoFile)
                playlist.add(videoFile)

        # If there are no videos in the playlist yet, then display an error
        if playlist.size() < 1:
            errorLocation = Settings.getScreensaverVideo()
            if Settings.isFolderSelection():
                errorLocation = Settings.getScreensaverFolder()

            log("No Screensaver file set or not valid %s" % errorLocation)
            xbmc.executebuiltin('XBMC.Notification(%s, %s, 5, %s)' % (__addon__.getLocalizedString(32300), errorLocation, __icon__))
            return None

        return playlist

    # Apply any user setting to the created playlist
    def _updatePlaylistForSettings(self, playlist):
        # Set the random start
        if Settings.isRandomStart() and playlist.size() > 0:
            filename = playlist[0].getfilename()
            duration = self._getVideoDuration(filename)

            log("Duration is %d for file %s" % (duration, filename))

            if duration > 10:
                listitem = xbmcgui.ListItem()
                # Record if the theme should start playing part-way through
                randomStart = random.randint(0, int(duration * 0.75))
                listitem.setProperty('StartOffset', str(randomStart))

                log("Setting Random start of %d for %s" % (randomStart, filename))

                # Remove the old item from the playlist
                playlist.remove(filename)
                # Add the new item at the start of the list
                playlist.add(filename, listitem, 0)

        return playlist

    # Update anything needed once the video is playing
    def _updatePostPlayingForSettings(self, playlist):
        # Check if we need to start at a random location
        if Settings.isRandomStart() and playlist.size() > 0:
            # Need to reset the offset to the start so that if it loops
            # it will play from the start
            playlist[0].setProperty('StartOffset', "0")

    # Returns the duration in seconds
    def _getVideoDuration(self, filename):
        duration = 0
        try:
            # Parse the video file for the duration
            duration = VideoParser().getVideoLength(filename)
        except:
            log("Failed to get duration from %s" % filename)
            log("Error: %s" % traceback.format_exc())
            duration = 0

        log("Duration retrieved is = %d" % duration)

        return duration

##################################
# Main of the Video Screensaver
##################################
if __name__ == '__main__':
    # Before we start, make sure that the settings have been updated correctly
    Settings.cleanAddonSettings()

    screenWindow = ScreensaverWindow.createScreensaverWindow()
    # Now show the window and block until we exit
    screenWindow.doModal()
    del screenWindow
    log("Leaving Screensaver Script")
