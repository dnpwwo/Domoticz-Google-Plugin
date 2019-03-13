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

Python version 3.4 or higher required & a 2019 version of Domoticz (for voice to work).  On Python 3.6.x this plugin will crash Domoticz 10-20% of the time when the plugin is stopped or restarted. This appears related to a defect introduced in Python 3.6 that has been reported on the internet.

To install:
* Go in your Domoticz directory using a command line and open the plugins directory.
* Run ```sudo pip3 install pychromecast```
* Run: ```git clone https://github.com/dnpwwo/Domoticz-Google-Plugin.git```
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
| Voice Device/Group | If specified device (or Audio Group) will receive audible notifications. 'Google_Devices' will appear as a notification target when editing any Domoticz device that supports Notifications |
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
| SendNotifiction | Target device speaks the message text e.g. ```commandArray['Lounge Home'] = "SendNotification 'Hello'"``` |

## Change log

| Version | Information |
| ----- | ---------- |
| 1.0.0 | Initial upload version |
| 1.1.2 | Actually functional (still WIP though). |
| 1.2.1 | Added parameters. |
| 1.3.5 | Initial voice message support. |
| 1.4.8 | Bugfix: Google Home Icon zip had an error in it.<br/>Improved voice support, added volume option |
| 1.5.3 | Bugfix: Plugin could hang during message handling, now does not wait forever.<br/>Messages are now spoken in the Domoticz UI language |
| 1.5.8 | Spoken messages are now queued.<br/>Manual load of site packages removed |
| 1.6.2 | Added SendNotification support to Domoticz scripts |
| 1.7.2 | Made onHeartbeat check device is still connected |
| 1.8.9 | Simplified threading, removed 'double connection' issue |
| 1.8.12 | Improved plugin shutdown on RPi |
| 1.9.1 | Added 'Quit' command |
| 1.9.7 | Improved error handling |
| 1.9.8 | Bugfix: handleMessage error when device not in list |
