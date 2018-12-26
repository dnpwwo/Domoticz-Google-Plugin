# Domoticz-Google Plugin
Full version of Google Chromecast & Home Python Plugin for Domoticz home automation

Controls multiple Google Chromecasts and Homes on your network.   Tested on Linux only.

## Key Features

* Devices are discovered automatically and created in the Devices tab
* When network connectivity is lost the Domoticz UI will optionally show the device(s) with Red banner
* Device icons are created in Domoticz
* Domoticz can control the Application selected
* Domoticz can control the Volume including Mute/Unmute
* Domoticz can control the playing media.  Play/Pause and skip forward and backwards

## Installation

Python version 3.4 or higher required & Domoticz version 3.87xx or greater.  On Python 3.6.x this plugin will crash Domoticz 10-20% of the time when the plugin is stopped or restarted. This appears related to a defect introduced in Python 3.6 that has been reported on the internet.

To install:
* Go in your Domoticz directory using a command line and open the plugins directory.
* Run ```sudo pip3 install pychromecast```
* Run: ```git clone https://github.com/dnpwwo/Domoticz-Google-Plugin.git```
* Restart Domoticz.

In the web UI, navigate to the Hardware page.  In the hardware dropdown there will be an entry called "Google Devices - Chromecast and Home".

## Updating

To update:
* Go in your Domoticz directory using a command line and open the plugins directory then the Domoticz-Google-Plugin directory.
* Run: ```git pull```
* Restart Domoticz.

## Configuration

### Google Chromecast & Home

Nothing !

### Domoticz

| Field | Information |
| ----- | ---------- |
| Notifications<br/>(future) | If true it will send audible notifications to the active devices |
| Notifier Name<br/>(future) | Only used if 'Notifications' is true. This name will appear in the list of notification targets when you use the 'Notifications' Button. Notifications you send to this target will appear on screen |
| Time Out Lost Devices | When true, the devices in Domoitcz will have a red banner when network connectivity is lost |
| Debug | When true the logging level will be much higher to aid with troubleshooting |

## Supported Commands

| Command | Information |
| ----- | ---------- |
| On | For 'Volume' Device - Turns mute off, <br/>For 'Playing' Device - Resume playback |
| Set Volume &lt;vol><br/>Set Level &lt;level&gt; | For 'Volume' Device - Sets volume percentage to &lt;vol&gt;, <br/>For 'Playing' Device - Sets position in media to &lt;level&gt; percent<br/>For Source device - Sets current Window |
| Play<br/>Playing | Resumes playing current media |
| Pause<br/>Paused | Pauses playing current media |
| Rewind | Sets position in current media back to the start |
| Stop<br/>Stopped | Stops playing current media |
| Trigger Playlist &lt;name&gt; &lt;position&gt;<br/>(future) | Start playing playlist &lt;name&gt; optionally at the supplied &lt;position&gt; |
| Off | For 'Volume' Device - Turns mute on, <br/>For 'Playing' Device - Pause playback |

## Change log

| Version | Information |
| ----- | ---------- |
| 1.0.0 | Initial upload version |
| 1.1.2 | Actually functional (still WIP though). |
