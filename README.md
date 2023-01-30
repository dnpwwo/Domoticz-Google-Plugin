# Domoticz-Google Plugin
Full version of Google Chromecast & Home Python Plugin for Domoticz home automation

Controls multiple Google Chromecasts and Homes on your network.   Tested on Linux only.

## Key Features

* Devices are discovered automatically and created in the Devices tab
* Voice notifications can be sent to selected Google triggered by Domoticz notifications 
* When network connectivity is lost the Domoticz UI will optionally show the device(s) with Red banner
* Device icons are created in Domoticz
* Domoticz can control the Application selected
* Domoticz can control the Volume including Mute/Unmute
* Domoticz can control the playing media.  Play/Pause and skip forward and backwards
* Google devices can be the targets of native Domoticz notifications in two different ways. Notifications are spoken in the language specified in Domoticz:
	* As a normal notification, these are sent to the device identified in the 'Voice Device/Group' hardware parameter
	* From a Domoticz event script targeting a specific device

## Installation

Python version 3.7.3 or higher required & a 2019 version of Domoticz (for voice to work).  On Python 3.6.x this plugin will crash Domoticz 10-20% of the time when the plugin is stopped or restarted. This appears related to a defect introduced in Python 3.6 that has been reported on the Internet.

To install:
* Go in your Domoticz directory using a command line.
* Run: ```cd plugins```
* Run ```sudo pip3 install pychromecast``` should be version 13.0.4 or greater
* Run ```sudo pip3 install gtts```
* Run: ```git clone https://github.com/dnpwwo/Domoticz-Google-Plugin.git```
* Verify that ```domoticz/plugins``` contains ```plugin.py``` and 2 icon files
* Restart Domoticz.

In the web UI, navigate to the Hardware page.  In the hardware dropdown there will be an entry called "Google Devices - Chromecast and Home".

To send voice notifications enter a Google device name in the 'Voice Device/Group' field in the hardware tab, then use the Domoticz standard Notification capability for individual Domoticz devices. Selecting notification target of 'Google_Devices' will cause the notification text to be spoken by the Google device.

## Updating

To update:
* Go in your Domoticz directory using a command line and open the plugins directory then the Domoticz-Google-Plugin directory.
* Run: ```git pull```
* Restart Domoticz.

## Configuration

### Google Chromecast & Home Devices

Nothing !

### Domoticz

| Field | Information |
| ----- | ---------- |
| Preferred Video/Audio Apps | Application to select when scripts request 'Video' or 'Audio' mode |
| Voice message volume | Volume to play messages (previous level will be restored afterwards) |
| Voice Device/Group | If specified device (or Audio Group) will receive audible notifications. The is the device's 'friendly name' as seen via the Google Home App. 'Google_Devices' will appear as a notification target when editing any Domoticz device that supports Notifications |
| Voice message IP address | Required for voice messages, the external address of the Domoticz host |
| Voice message port | Required for voice messages, the port to use to serve the message to the Google device(s) |
| Time Out Lost Devices | When true, the devices in Domoitcz will have a red banner when network connectivity is lost |
| Log to file | When true, messages from Google devices are written to Messages.log in the Plugin's directory |
| Debug | When true the logging level will be much higher to aid with troubleshooting |

## Supported Script Commands

| Command | Information |
| ----- | ---------- |
| On | For 'Volume' Device - Turns mute off, <br/>For 'Playing' Device - Resume playback |
| Set Volume &lt;vol><br/>Set Level &lt;level&gt; | For 'Volume' Device - Sets volume percentage to &lt;vol&gt;, <br/>For 'Playing' Device - Sets position in media to &lt;level&gt; percent<br/>For Source device - Sets current Window |
| Play<br/>Playing | Resumes playing current media |
| Pause<br/>Paused | Pauses playing current media |
| Rewind | Sets position in current media back to the start |
| Stop<br/>Stopped | Stops playing current media |
| Trigger &lt;URL&gt; | Start playing &lt;URL&gt; |
| Video | Switch device to the selected Video App |
| Audio | Switch device to the selected Audio App |
| Quit | Quits the current application on the device |
| Off | For 'Volume' Device - Turns mute on, <br/>For 'Playing' Device - Pause playback |
| SendNotifiction | Target device speaks the message text e.g. ```commandArray['Lounge Home'] = "SendNotification Good morning"``` |

## Change log

| Version | Information |
| ----- | ---------- |
| 1.13.1 | Bugfix: Plugin now waits for voice playback correctly |
| 1.14.7 | Bugfix: Long media file now play |
| 1.15.3 | Improved logging during mp3 transfer |
| 1.16.13 | Bugfix: Handle groups changing 'elected leader' |
| 1.18.13 | Revamped device updates + improved debugging |
| 1.18.35 | Bugfix: Stopped devices being marked 'Off', fixed Playing slider |
| 1.18.37 | Bugfix: Media text not showing correctly |
| 1.19.5 | Removed Address & Port parameters because they seemed to confuse people. Now determined internally. |
| 1.22.0 | Support newer versions of PyChromeCast where the host is not available |
| 2.0.2 | Support newer versions of PyChromeCast (13.0.4) and related imports |
| 2.0.3 | Suppress occasional TypeError in UpdatePlaying function |
