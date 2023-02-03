# Google Devices
#
# Listens for chromecast and home devices and monitors the ones it finds.
# New ones are added automatically and named using their friendly name
#
# Author: Dnpwwo, 2019
#         Based on the Domoticz plugin authored by Tsjippy (https://github.com/Tsjippy)
#         Huge shout out to Paulus Shoutsen (https://github.com/balloob) for his pychromecast library that does all the hard work
#         And Fred Clift (https://github.com/minektur) who wrote the initial communication layer
#         Credit where it is due!
#
"""
<plugin key="GoogleDevs" name="Google Devices - Chromecast and Home" author="dnpwwo" version="2.0.5" wikilink="https://github.com/dnpwwo/Domoticz-Google-Plugin" externallink="https://store.google.com/product/chromecast">
    <description>
        <h2>Domoticz Google Plugin</h2><br/>
        <h3>Key Features</h3>
        <ul style="list-style-type:square">
            <li style="line-height:normal">Devices are discovered automatically and created in the Devices tab</li>
            <li style="line-height:normal">When network connectivity is lost the Domoticz UI will optionally show the device(s) with Red banner</li>
            <li style="line-height:normal">Device icons are created in Domoticz</li>
            <li style="line-height:normal">Domoticz can control the Application selected</li>
            <li style="line-height:normal">Domoticz can control the Volume including Mute/Unmute</li>
            <li style="line-height:normal">Domoticz can control the playing media.  Play/Pause and skip forward and backwards</li>
            <li style="line-height:normal">Google devices can be the targets of native Domoticz notifications. These are spoken through a specified device (or audio group) in the language specified in Domoticz </li>
            <li style="line-height:normal">Voice notifications can be sent to selected Google devices from event scripts (Lua or Python)</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li style="line-height:normal">Status - Basic status indicator, On/Off.</li>
            <li style="line-height:normal">Volume - Icon mutes/unmutes, slider shows/sets volume</li>
            <li style="line-height:normal">Source - Selector switch for content source (App)</li>
            <li style="line-height:normal">Playing - Icon Pauses/Resumes, slider shows/sets percentage through media</li>
        </ul>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li style="line-height:normal">Preferred Video/Audio Apps - Application to select when scripts request 'Video' or 'Audio' mode from a script</li>
            <li style="line-height:normal">Voice message volume - Volume to play messages (previous level will be restored afterwards)</li>
            <li style="line-height:normal">Voice Device/Group - If specified device (or Audio Group) will receive audible notifications. 'Google_Devices' will appear as a notification target when editing any Domoticz device that supports Notifications</li>
            <li style="line-height:normal">Time Out Lost Devices - When true, the devices in Domoticz will have a red banner when network connectivity is lost</li>
            <li style="line-height:normal">Log to file - When true, messages from Google devices are written to Messages.log in the Plugin's directory</li>
            <li style="line-height:normal">Debug - When true the logging level will be much higher to aid with troubleshooting</li>
        </ul>
    </description>
    <params>
        <param field="Mode2" label="Preferred Video/Audio Apps" width="150px">
            <options>
                <option label="Netflix / Spotify" value="{|Video|:|Netflix|,|Audio|:|Spotify|}" default="true"/>
                <option label="Youtube / Spotify" value="{|Video|:|Youtube|,|Audio|:|Spotify|}" />
                <option label="Netflix / Youtube" value="{|Video|:|Netflix|,|Audio|:|Youtube|}" />
                <option label="Youtube / Youtube" value="{|Video|:|Youtube|,|Audio|:|Youtube|}" />
                <option label="None" value="{|Video|:||,|Audio|:||}" />
            </options>
        </param>
        <param field="Mode3" label="Voice message volume" width="50px" required="true">
            <options>
                <option label="10%" value="10" />
                <option label="20%" value="20" />
                <option label="30%" value="30" />
                <option label="40%" value="40" />
                <option label="50%" value="50" default="true"/>
                <option label="60%" value="60" />
                <option label="70%" value="70" />
                <option label="80%" value="80" />
                <option label="90%" value="90" />
                <option label="100%" value="100" />
            </options>
        </param>
        <param field="Mode1" label="Voice Device/Group" width="150px" />
        <param field="Mode4" label="Time Out Lost Devices" width="75px">
            <options>
                <option label="True" value="True" default="true"/>
                <option label="False" value="False" />
            </options>
        </param>
        <param field="Mode5" label="Log to file" width="75px">
            <options>
                <option label="True" value="True"/>
                <option label="False" value="False" default="true"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz

import sys,os
import threading
import time
import json
import queue
import random
import pychromecast
import pychromecast.config as Consts
try:
    from gtts import gTTS
    voiceEnabled = True
except Exception as err:
    voiceEnabled = False
    voiceError = str(err)

KB_TO_XMIT = 1024 * 16

DEV_STATUS  = "-1"
DEV_VOLUME  = "-2"
DEV_PLAYING = "-3"
DEV_SOURCE  = "-4"

APP_NONE=0
APP_OTHER=40
Apps={ 'Backdrop':Consts.APP_BACKDROP, 'Spotify':'CC32E753', 'Netflix':'CA5E8412', 'Youtube':Consts.APP_YOUTUBE, 'Other':'' }

# Language overrides for when Domoticz language does not line up with Google translate
# Dictionary should contain Domoticz language string as key and language string to be used e.g {"nl":"nl-NL"}
langOverride = {}

class GoogleDevice:
    def __init__(self, googleDevice):
        self.Name = googleDevice.name
        self.Model = googleDevice.model_name
        self.UUID = str(googleDevice.uuid)
        self.GoogleDevice = googleDevice
        self.Ready = False
        self.Active = False
        self.LogToFile("Google device created: "+str(self))
        self.State = {}
        
        googleDevice.register_status_listener(self.CastStatusListener(self))
        googleDevice.media_controller.register_status_listener(self.MediaStatusListener(self))
        googleDevice.register_connection_listener(self.ConnectionListener(self))
        googleDevice.start()

    class CastStatusListener:
        def __init__(self, parent):
            self.parent = parent

        def new_cast_status(self, status):
            global Apps
            # CastStatus(is_active_input=False, is_stand_by=True, volume_level=0.5049999952316284, volume_muted=False, app_id=None, display_name=None, namespaces=[], session_id=None, transport_id=None, status_text='')
            try:
                if (status==None): return

                self.parent.LogToFile(status)
                self.parent.Ready = True
                
                for Unit in Devices:
                    if (Devices[Unit].DeviceID.find(self.parent.UUID+DEV_STATUS) >= 0):
                        if  (status.display_name == None) or (status.display_name == 'Backdrop'):
                            self.Active = False
                            nValue = 9
                            sValue = 'Screensaver'
                            UpdateDevice(Unit, nValue, sValue, Devices[Unit].TimedOut)
                        else:
                            UpdateDevice(Unit, Devices[Unit].nValue, status.display_name, Devices[Unit].TimedOut)

                    elif (Devices[Unit].DeviceID.find(self.parent.UUID+DEV_VOLUME) >= 0):
                        nValue = 2
                        if (status.volume_muted == True):
                            nValue = 0
                        sValue = int(status.volume_level*100)
                        UpdateDevice(Unit, nValue, str(sValue), Devices[Unit].TimedOut)

                    elif (Devices[Unit].DeviceID.find(self.parent.UUID+DEV_SOURCE) >= 0):
                        nValue = sValue = APP_NONE
                        if (status.display_name != None) and (status.app_id != Consts.APP_BACKDROP):
                            if Devices[Unit].Options['LevelNames'].find(status.display_name) == -1:
                                nValue = sValue = len(Devices[Unit].Options['LevelNames'].split("|"))*10
                                Devices[Unit].Options['LevelNames'] = Devices[Unit].Options['LevelNames']+"|"+status.display_name
                                Devices[Unit].Update(nValue, str(sValue), Options=Devices[Unit].Options)
                                
                                # remember all apps that we see because we may need the ID again later
                                seenApps = getConfigItem("Apps", Apps)
                                if not status.display_name in seenApps:
                                    seenApps[status.display_name] = status.app_id
                                    setConfigItem("Apps", seenApps)
                            else:
                                for i, level in enumerate(Devices[Unit].Options['LevelNames'].split("|")):
                                    if level == status.display_name:
                                        nValue = sValue = i*10
                                        break
                        
                        UpdateDevice(Unit, nValue, str(sValue), Devices[Unit].TimedOut)
                        
            except RuntimeError: # dictionary sizes can be changed mid loop
                pass
            except Exception as err:
                Domoticz.Error("new_cast_status: "+str(err))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                Domoticz.Error(str(exc_type)+", "+fname+", Line: "+str(exc_tb.tb_lineno))
                Domoticz.Error(str(status))

    class MediaStatusListener:
        def __init__(self, parent):
            self.parent = parent

        def new_media_status(self, status):
            # <MediaStatus {'metadata_type': 3, 'title': 'The Chainsmokers / Coldplay - Something Just Like This', 'series_title': None, 'season': None, 'episode': None, 'artist': 'Nova 100', 'album_name': None, 'album_artist': None, 'track': None, 'subtitle_tracks': [{'trackId': 1, 'type': 'AUDIO'}], 'images': [MediaImage(url='http://cdn-profiles.tunein.com/s17634/images/logoq.png', height=None, width=None)], 'supports_pause': True, 'supports_seek': False, 'supports_stream_volume': True, 'supports_stream_mute': True, 'supports_skip_forward': False, 'supports_skip_backward': False, 'current_time': 35.356328, 'content_id': 'http://playerservices.streamtheworld.com/api/livestream-redirect/NOVA_100_AAC48.aac?src=tunein&tdtok=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiIsImtpZCI6ImZTeXA4In0.eyJpc3MiOiJ0aXNydiIsInN1YiI6IjIxMDY0IiwiaWF0IjoxNTU1NzI1MDY2LCJ0ZC1yZWciOmZhbHNlfQ.6c9J7oN_pQWvZUp6cAn6GkMEl4QrQDP_jV-6cVUAXDE', 'content_type': 'audio/mp3', 'duration': None, 'stream_type': 'LIVE', 'idle_reason': None, 'media_session_id': 1, 'playback_rate': 1, 'player_state': 'PLAYING', 'supported_media_commands': 274445, 'volume_level': 1, 'volume_muted': False, 'media_custom_data': {'contentId': 's17634'}, 'media_metadata': {'metadataType': 3, 'title': 'The Chainsmokers / Coldplay - Something Just Like This', 'artist': 'Nova 100', 'images': [{'url': 'http://cdn-profiles.tunein.com/s17634/images/logoq.png'}], 'subtitle': 'Nova 100'}, 'current_subtitle_tracks': [], 'last_updated': datetime.datetime(2019, 4, 20, 1, 51, 45, 446836)}>
            try:
                if (status==None): return

                self.parent.LogToFile(status)
                self.parent.Ready = True

                for Unit in Devices:
                    if (Devices[Unit].DeviceID.find(self.parent.UUID) >= 0):
                        nValue = Devices[Unit].nValue
                        sValue = Devices[Unit].sValue
                        if (Devices[Unit].DeviceID.find(self.parent.UUID+DEV_STATUS) >= 0):    # Overall Status
                            liveStream = ""
                            if status.stream_type_is_live: liveStream = "[Live] "
                            if (status.media_is_generic):
                                nValue = 4
                                sValue = liveStream + stringOrBlank(status.title)
                            elif (status.media_is_tvshow):
                                nValue = 4
                                sValue = liveStream+stringOrBlank(status.series_title)+"[S"+stringOrBlank(status.season)+":E"+ stringOrBlank(status.episode)+"] "+ stringOrBlank(status.title)
                            elif (status.media_is_movie):
                                nValue = 4
                                sValue = liveStream + stringOrBlank(status.title)
                            elif (status.media_is_photo):
                                nValue = 6
                                sValue = stringOrBlank(status.title)
                            elif (status.media_is_musictrack):
                                nValue = 5
                                sValue = liveStream+stringOrBlank(status.artist)+ " ("+stringOrBlank(status.album_name)+") "+ stringOrBlank(status.title)

                            # Check to see if we are paused
                            if (status.player_is_paused): nValue = 2

                            # Now tidy up and compress the string
                            sValue = sValue.lstrip(":")
                            sValue = sValue.rstrip(", :")
                            sValue = sValue.replace("()", "")
                            sValue = sValue.replace("[] ", "")
                            sValue = sValue.replace("[S:E] ", "")
                            sValue = sValue.replace("  ", " ")
                            sValue = sValue.replace(", :", ":")
                            sValue = sValue.replace(", (", " (")
                            if (len(sValue) > 40): sValue = sValue.replace(", ", ",")
                            if (len(sValue) > 40): sValue = sValue.replace(" (", "(")
                            if (len(sValue) > 40): sValue = sValue.replace(") ", ")")
                            if (len(sValue) > 40): sValue = sValue.replace(": ", ":")
                            if (len(sValue) > 40): sValue = sValue.replace(" [", "[")
                            if (len(sValue) > 40): sValue = sValue.replace("] ", "]")
                            sValue = sValue.replace(",(", "(")
                            sValue = sValue.strip()
                            if (len(sValue) == 0): sValue = Devices[Unit].sValue
                            UpdateDevice(Unit, nValue, str(sValue), Devices[Unit].TimedOut)

                        elif (Devices[Unit].DeviceID.find(self.parent.UUID+DEV_PLAYING) >= 0):   # Playing
                            if (status.duration == None) or (status.current_time == None):
                                sValue='0'
                            else:
                                try:
                                    sValue=str(int((status.adjusted_current_time / status.duration)*100))
                                except ZeroDivisionError as Err:
                                    sValue='0'
                                except TypeError as Err:
                                    sValue='0'
                            if (status.player_is_playing):
                                nValue=2
                                if (sValue=='0'): sValue='1'
                            elif (status.player_is_paused):
                                nValue=0
                                if (sValue=='0'): sValue='1'
                            else:
                                nValue=0
                                sValue='0'
                            UpdateDevice(Unit, nValue, str(sValue), Devices[Unit].TimedOut)

            except RuntimeError: # dictionary sizes can be changed mid loop
                pass
            except Exception as err:
                Domoticz.Error("new_media_status: "+str(err))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                Domoticz.Error(str(exc_type)+", "+fname+", Line: "+str(exc_tb.tb_lineno))
                Domoticz.Error(str(status))

    class ConnectionListener:
        def __init__(self, parent):
            self.parent = parent

        def new_connection_status(self, new_status):
            try:
                self.parent.LogToFile(new_status)
                Domoticz.Status(self.parent.Name+" is now: "+str(new_status))
                if (new_status.status == "DISCONNECTED") or (new_status.status == "LOST") or (new_status.status == "FAILED"):
                    self.parent.Ready = False
                    self.parent.Active = False
                    
                if (Parameters["Mode4"] != "False"):
                    for Unit in Devices:
                        if (Devices[Unit].DeviceID.find(self.parent.UUID) >= 0):
                            UpdateDevice(Unit, Devices[Unit].nValue, Devices[Unit].sValue, (1,0)[new_status.status=="CONNECTED"])
                            
            except Exception as err:
                Domoticz.Error("new_connection_status: "+str(err))
                Domoticz.Error("new_connection_status: "+str(new_status))

    def LogToFile(self, status):
        if (Parameters["Mode5"] != "False") and (status != None):
            print(time.strftime('%Y-%m-%d %H:%M:%S')+" ["+self.Name+"] "+str(status), file=open(Parameters["HomeFolder"]+"Messages.log", "a"))
        
    @property
    def VolumeUnit(self):
        global DEV_VOLUME
        # find first device
        for Unit in Devices:
            if (Devices[Unit].DeviceID == self.UUID+DEV_VOLUME):
                return Unit
        return None

    @property
    def PlayingUnit(self):
        global DEV_PLAYING
        # find first device
        for Unit in Devices:
            if (Devices[Unit].DeviceID == self.UUID+DEV_PLAYING):
                return Unit
        return None

    def UpdatePlaying(self):
        if (self.GoogleDevice.media_controller.status != None) and (self.GoogleDevice.media_controller.status.duration != None):
            if (self.GoogleDevice.media_controller.status.player_is_playing):
                try:
                    sValue=str(int((self.GoogleDevice.media_controller.status.adjusted_current_time / self.GoogleDevice.media_controller.status.duration)*100))
                    Unit = self.PlayingUnit
                    if (Unit != None): UpdateDevice(Unit, Devices[Unit].nValue, str(sValue), Devices[Unit].TimedOut)
                except ZeroDivisionError as Err:
                    pass
                except TypeError as Err:
                    pass
                except Exception as err:
                    Domoticz.Error("UpdatePlaying: "+str(err))
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    Domoticz.Error(str(exc_type)+", "+fname+", Line: "+str(exc_tb.tb_lineno))
        
    def StoreState(self):
        self.State.clear()
        if (self.GoogleDevice.status != None):
            self.State['Volume'] = self.GoogleDevice.status.volume_level
            self.State['Muted'] = self.GoogleDevice.status.volume_muted
            self.State['App'] = self.GoogleDevice.app_id
        if (self.GoogleDevice.media_controller.status != None):
            self.State['SupportsSeek'] = self.GoogleDevice.media_controller.status.supports_seek

        self.GoogleDevice.quit_app()
        self.GoogleDevice.set_volume(int(Parameters["Mode3"]) / 100)
        self.GoogleDevice.set_volume_muted(False)       
        
    def RestoreState(self):
        if (self.State['Volume'] != None):
            self.GoogleDevice.quit_app()
            if 'Volume' in self.State: self.GoogleDevice.set_volume(self.State['Volume'])
            if 'Muted' in self.State: self.GoogleDevice.set_volume_muted(self.State['Muted'])
        else:
            Domotic.Log("No device state to restore after notification")
        
    def __str__(self):
        return "'%s', Model: '%s', UUID: '%s'" % (self.Name, self.Model, self.UUID)

class BasePlugin:
    
    def __init__(self):
        global voiceEnabled
        self.googleDevices = {}
        self.stopDiscovery = None
        self.messageServer = None
        self.messageQueue = None
        if (voiceEnabled):
            self.messageQueue = queue.Queue()
            self.messageThread = threading.Thread(name="GoogleNotify", target=BasePlugin.handleMessage, args=(self,))

    def handleMessage(self):
        global voiceEnabled
        Domoticz.Debug("handleMessage: Entering notification handler")
        ipAddress = GetIP()
        ipPort = str(random.randint(10001,19999))
        
        if (len(ipAddress) > 0):
            Domoticz.Log("Notifications will use IP Address: "+ipAddress+":"+ipPort+" to serve audio media.")
            self.messageServer = Domoticz.Connection(Name="Message Server", Transport="TCP/IP", Protocol="HTTP", Port=ipPort)
            self.messageServer.Listen()
        else:
            Domoticz.Error("Unable to determine host external IP address: Voice notifications will not be enabled")
            voiceEnabled = False

        while voiceEnabled:
            try:
                Message = self.messageQueue.get(block=True)
                if Message is None:
                    self.messageQueue.task_done()
                    break

                if (not os.path.exists(Parameters['HomeFolder']+'Messages')):
                    os.mkdir(Parameters['HomeFolder']+'Messages')
                Domoticz.Debug("handleMessage: '"+Message["Text"]+"', to be sent to '"+Message["Target"]+"'")
                
                for uuid in self.googleDevices:
                    if (self.googleDevices[uuid].GoogleDevice.name == Message["Target"]):
                        if (self.googleDevices[uuid].Ready):
                            language = Parameters["Language"]
                            if (language in langOverride): language = langOverride[language]
                            tts = gTTS(Message["Text"],lang=language)
                            messageFileName = Parameters['HomeFolder']+'Messages/'+uuid+'.mp3'
                            tts.save(messageFileName)
                            if (not os.path.exists(messageFileName)):
                                Domoticz.Error("'"+messageFileName+"' not found, translation must have failed.")
                                break
                            else:
                                Domoticz.Debug("'"+messageFileName+"' created, "+str(os.path.getsize(messageFileName))+" bytes")
                            
                            self.googleDevices[uuid].StoreState()
                            mc = self.googleDevices[uuid].GoogleDevice.media_controller
                            mc.play_media("http://"+ipAddress+":"+ipPort+"/"+uuid+".mp3", 'audio/mp3')
                            mc.block_until_active()
                            time.sleep(1.0)
                            endTime = time.time() + 10
                            while (mc.status.player_is_idle) and (time.time() < endTime):
                                Domoticz.Debug("Waiting for player (timeout in "+str(endTime - time.time())[:4]+" seconds)")
                                time.sleep(0.5)
                            if (mc.status.duration != None):
                                endTime = time.time()+mc.status.duration+1
                            while (time.time() < endTime) and (not mc.status.player_is_idle):
                                if (mc.status.duration != None):
                                    Domoticz.Debug("Waiting for message to complete playing ("+str(mc.status.adjusted_current_time)[:4]+" of "+str(mc.status.duration)+", timeout in "+str(endTime - time.time())[:4]+" seconds)")
                                else:
                                    Domoticz.Debug("Waiting for message to complete playing (unknown duration, timeout in "+str(endTime - time.time())[:4]+" seconds)")
                                time.sleep(0.5)
                            self.googleDevices[uuid].RestoreState()
                                
                            if (time.time() < endTime):
                                Domoticz.Log("Notification sent to '"+Message["Target"]+"' completed")
                                os.remove(messageFileName)
                            else:
                                Domoticz.Error("Notification sent to '"+Message["Target"]+"' timed out")
                        else:
                            Domoticz.Error("Google device '"+Message["Target"]+"' is not connected, ignored.")
                    
            except Exception as err:
                Domoticz.Error("handleMessage: "+str(err))
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                Domoticz.Error(str(exc_type)+", "+fname+", Line: "+str(exc_tb.tb_lineno))
            self.messageQueue.task_done()
        
        if (self.messageServer != None): self.messageServer.Disconnect()
        Domoticz.Debug("handleMessage: Exiting notification handler")
    
    def discoveryCallback(self, googleDevice):
        global DEV_STATUS,DEV_VOLUME,DEV_PLAYING,DEV_SOURCE
        try:
            uuid = str(googleDevice.uuid)
            if (uuid in self.googleDevices):
                # Happens for groups when 'elected leader' changes
                self.googleDevices[uuid].GoogleDevice.disconnect()
                self.googleDevices[uuid].GoogleDevice = None
                del self.googleDevices[uuid]

            self.googleDevices[uuid] = GoogleDevice(googleDevice)
            
            createDomoticzDevice = True
            maxUnitNo = 1
            for Device in Devices:
                if (Devices[Device].Unit > maxUnitNo): maxUnitNo = Devices[Device].Unit
                if (Devices[Device].DeviceID.find(uuid) >= 0):
                    createDomoticzDevice = False
                    # Check that the device name hasn't changed
                    if (self.googleDevices[uuid].Name != Devices[Device].Name[0:len(self.googleDevices[uuid].Name)]):
                        Domoticz.Log("Device name mismatch: '%s' vs '%s'" % (self.googleDevices[uuid].Name,Devices[Device].Name))

            if (createDomoticzDevice):
                logoType = Parameters['Key']+'Chromecast'
                if (googleDevice.model_name.find("Home") >= 0) or (googleDevice.model_name == "Google Cast Group"): logoType = Parameters['Key']+'HomeMini'
                Domoticz.Log("Creating devices for '"+googleDevice.name+"' of type '"+googleDevice.model_name+"' in Domoticz, look in Devices tab.")
                Domoticz.Device(Name=self.googleDevices[uuid].Name+" Status", Unit=maxUnitNo+1, Type=17, Switchtype=17, Image=Images[logoType].ID, DeviceID=uuid+DEV_STATUS, Description=googleDevice.model_name, Used=0).Create()
                Domoticz.Device(Name=self.googleDevices[uuid].Name+" Volume", Unit=maxUnitNo+2, Type=244, Subtype=73, Switchtype=7, Image=8, DeviceID=uuid+DEV_VOLUME, Description=googleDevice.model_name, Used=0).Create()
                Domoticz.Device(Name=self.googleDevices[uuid].Name+" Playing", Unit=maxUnitNo+3, Type=244, Subtype=73, Switchtype=7, Image=12, DeviceID=uuid+DEV_PLAYING, Description=googleDevice.model_name, Used=0).Create()
                if (googleDevice.model_name.find("Chromecast") >= 0):
                    Options = {"LevelActions": "", "LevelNames": "Off", "LevelOffHidden": "false", "SelectorStyle": "0"}
                    Domoticz.Device(Name=self.googleDevices[uuid].Name+" Source",  Unit=maxUnitNo+4, TypeName="Selector Switch", Switchtype=18, Image=12, DeviceID=uuid+DEV_SOURCE, Description=googleDevice.model_name, Used=0, Options=Options).Create()
                elif (googleDevice.model_name.find("Google Home") >= 0) or (googleDevice.model_name == "Google Cast Group"):
                    pass
                else:
                    Domoticz.Error("Unsupported device type: "+str(self.googleDevices[uuid]))
                
        except Exception as err:
            Domoticz.Error("discoveryCallback: "+str(err))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            Domoticz.Error(str(exc_type) + ": " + fname + " at " + str(exc_tb.tb_lineno))
    
    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()

        Parameters["Mode2"] = json.loads(Parameters["Mode2"].replace('|','"'))
        
        if Parameters['Key']+'Chromecast' not in Images: Domoticz.Image('ChromecastUltra.zip').Create()
        if Parameters['Key']+'HomeMini' not in Images: Domoticz.Image('GoogleHomeMini.zip').Create()
        
        # Mark devices as timed out
        if Parameters["Mode4"] != "False":
            for Device in Devices:
                UpdateDevice(Device, Devices[Device].nValue, Devices[Device].sValue, 1)

        if Parameters["Mode1"] != "":
            Domoticz.Notifier("Google_Devices")

        # Non-blocking asynchronous discovery, Nice !
        self.stopDiscovery = pychromecast.get_chromecasts(callback=self.discoveryCallback, blocking=False)
        
        if (voiceEnabled):
            self.messageThread.start()
        else:
            Domoticz.Error("'gtts' module import error: "+voiceError+": Voice notifications will not be enabled")

    def onMessage(self, Connection, Data):
    
        try:
            if (Connection.Parent == self.messageServer):
                connectionOkay = True
        except AttributeError:
            Domoticz.Error("Please upgrade to the latest beta!!")
            connectionOkay = True

        # Callback connection for audible notifications
        if (connectionOkay):
            messageFile = None
            try:
                headerCode = "200 OK"
                if (not 'Verb' in Data):
                    Domoticz.Error("Invalid web request received, no Verb present")
                    headerCode = "400 Bad Request"
                elif (Data['Verb'] != 'GET'):
                    Domoticz.Error("Invalid web request received, only GET requests allowed ("+Data['Verb']+")")
                    headerCode = "405 Method Not Allowed"
                elif (not 'URL' in Data):
                    Domoticz.Error("Invalid web request received, no URL present")
                    headerCode = "400 Bad Request"
                elif (not 'Headers' in Data):
                    Domoticz.Error("Invalid web request received, no Headers present")
                    headerCode = "400 Bad Request"
                elif (not 'Range' in Data['Headers']):
                    Domoticz.Error("Invalid web request received, no Range header present")
                    headerCode = "400 Bad Request"
                elif (not os.path.exists(Parameters['HomeFolder']+'Messages'+Data['URL'])):
                    Domoticz.Error("Invalid web request received, file '"+Parameters['HomeFolder']+'Messages'+Data['URL']+"' does not exist")
                    headerCode = "404 File Not Found"
                
                if (headerCode != "200 OK"):
                    DumpHTTPResponseToLog(Data)
                    Connection.Send({"Status": headerCode})
                else:
                    # 'Range':'bytes=0-'
                    range = Data['Headers']['Range']
                    fileStartPosition = int(range[range.find('=')+1:range.find('-')])
                    messageFileName = Parameters['HomeFolder']+'Messages'+Data['URL']
                    messageFileSize = os.path.getsize(messageFileName)
                    messageFile = open(messageFileName, mode='rb')
                    messageFile.seek(fileStartPosition)
                    fileContent = messageFile.read(KB_TO_XMIT)
                    Domoticz.Debug(Connection.Address+":"+Connection.Port+" Sent 'GET' request file '"+Data['URL']+"' from position "+str(fileStartPosition)+", "+str(len(fileContent))+" bytes will be returned")
                    if (len(fileContent) == KB_TO_XMIT):
                        headerCode = "206 Partial Content"
                    Connection.Send({"Status":headerCode, "Headers": {"Content-Type": "audio/mp3", "Content-Range": "bytes "+str(fileStartPosition)+"-"+str(messageFile.tell())+"/"+str(messageFileSize)}, "Data":fileContent})
                    
            except Exception as inst:
                Domoticz.Error("Exception detail: '"+str(inst)+"'")
                DumpHTTPResponseToLog(Data)
                
            if (messageFile != None):
                messageFile.close()
        else:
            Domoticz.Error("Message from unknown connection: "+str(Connection))

    def onCommand(self, Unit, Command, Level, Hue):
        global DEV_STATUS,DEV_VOLUME,DEV_PLAYING,DEV_SOURCE
        global APP_OTHER
        global Apps
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        
        Command = Command.strip()
        action, sep, params = Command.partition(' ')
        action = action.capitalize()

        # Map Unit number back to underlying Google device
        uuid = Devices[Unit].DeviceID[:-2]
        subUnit = Devices[Unit].DeviceID[-2:]
        # self.googleDevices[uuid]
        Domoticz.Debug("UUID: "+str(uuid)+", sub unit: "+subUnit+", Action: "+action+", params: "+params)

        if (action == 'On'):
            if (subUnit == DEV_VOLUME):
                self.googleDevices[uuid].GoogleDevice.set_volume_muted(False)
            elif (subUnit == DEV_PLAYING):
                self.googleDevices[uuid].GoogleDevice.media_controller.play()
        elif (action == 'Off'):
            if (subUnit == DEV_VOLUME):
                self.googleDevices[uuid].GoogleDevice.set_volume_muted(True)
            elif (subUnit == DEV_PLAYING):
                self.googleDevices[uuid].GoogleDevice.media_controller.pause()
            elif (subUnit == DEV_SOURCE):
                self.googleDevices[uuid].GoogleDevice.quit_app()
        elif (action == 'Set'):
            if (params.capitalize() == 'Level') or (Command.lower() == 'Volume'):
                if (subUnit == DEV_VOLUME):
                    currentVolume = self.googleDevices[uuid].GoogleDevice.status.volume_level
                    newVolume = Level / 100
                    if (currentVolume > newVolume):
                        self.googleDevices[uuid].GoogleDevice.volume_down(currentVolume-newVolume)
                    else:
                        self.googleDevices[uuid].GoogleDevice.volume_up(newVolume-currentVolume)
                elif (subUnit == DEV_PLAYING):
                        if (self.googleDevices[uuid].GoogleDevice.media_controller.status.duration!=None):
                            newPosition = self.googleDevices[uuid].GoogleDevice.media_controller.status.duration * (Level/100)
                            self.googleDevices[uuid].GoogleDevice.media_controller.seek(newPosition)
                        else:
                            Domoticz.Log("["+self.googleDevices[uuid].Name+"] No duration found, seeking is not possible at this time.")
                elif (subUnit == DEV_SOURCE):
                    seenApps = getConfigItem("Apps", Apps)
                    for i, appName in enumerate(Devices[Unit].Options['LevelNames'].split("|")):
                        if i*10 == Level:
                            if (seenApps[appName]!=''):
                                self.googleDevices[uuid].GoogleDevice.start_app(seenApps[appName])
                            break
                    
        elif (action == 'Rewind'):
            self.googleDevices[uuid].GoogleDevice.media_controller.seek(0.0)
        elif (action == 'Play') or (action == 'Playing'):
            self.googleDevices[uuid].GoogleDevice.media_controller.play()
        elif (action == 'Pause') or (action == 'Paused'):
            self.googleDevices[uuid].GoogleDevice.media_controller.pause()
        elif (action == 'Trigger'):
            #mc.play_media('http://'+str(self.ip)+':'+str(self.Port)+'/message.mp3', 'music/mp3')
            x = 1
        elif (action == 'Video'): # Blockly command
            if (self.googleDevices[uuid].GoogleDevice.app_display_name != '') and (self.googleDevices[uuid].GoogleDevice.app_display_name != Parameters["Mode2"]["Video"]):
                self.googleDevices[uuid].GoogleDevice.quit_app()
                seenApps = getConfigItem("Apps", Apps)
                if (Parameters["Mode2"]["Video"] in seenApps):
                    self.googleDevices[uuid].GoogleDevice.start_app(seenApps[Parameters["Mode2"]["Video"]])
        elif (action == 'Audio'): # Blockly command
            if (self.googleDevices[uuid].GoogleDevice.app_display_name != '') and (self.googleDevices[uuid].GoogleDevice.app_display_name != Parameters["Mode2"]["Audio"]):
                self.googleDevices[uuid].GoogleDevice.quit_app()
                seenApps = getConfigItem("Apps", Apps)
                if (Parameters["Mode2"]["Audio"] in seenApps):
                    self.googleDevices[uuid].GoogleDevice.start_app(seenApps[Parameters["Mode2"]["Audio"]])
        elif (action == 'Sendnotification'):
            if (self.messageQueue != None):
                self.messageQueue.put({"Target":self.googleDevices[uuid].GoogleDevice.device.friendly_name, "Text":params})
            else:
                Domoticz.Error("Message queue not initialized, notification ignored.")
        elif (action == 'Quit'):
            self.googleDevices[uuid].GoogleDevice.quit_app()

    def onHeartbeat(self):
        for uuid in self.googleDevices:
            self.googleDevices[uuid].UpdatePlaying()

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("onNotification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)
        if (self.messageQueue != None):
            self.messageQueue.put({"Target":Parameters['Mode1'], "Text":Text})
        else:
            Domoticz.Error("Message queue not initialized, notification ignored.")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug(Connection.Address+":"+Connection.Port+" Connection established")
            
    def onDisconnect(self, Connection):
        Domoticz.Debug(Connection.Address+":"+Connection.Port+" Connection disconnected")
            
    def onStop(self):
        if (self.messageQueue != None):
            Domoticz.Log("Clearing notification queue (approximate size "+str(self.messageQueue.qsize())+" entries)...")
            self.messageQueue.put(None)
        
        for uuid in self.googleDevices:
            try:
                Domoticz.Log(self.googleDevices[uuid].Name+" Disconnecting...")
                self.googleDevices[uuid].GoogleDevice.disconnect(blocking=False)
            except Exception as err:
                Domoticz.Error("onStop: "+str(err))
                
        if (self.stopDiscovery != None):
            Domoticz.Log("Zeroconf Discovery Stopping...")
            self.stopDiscovery()
            
        Domoticz.Log("Threads still active: "+str(threading.active_count())+", should be 1.")
        endTime = time.time() + 70
        while (threading.active_count() > 1) and (time.time() < endTime):
            for thread in threading.enumerate():
                if (thread.name != threading.current_thread().name):
                    Domoticz.Log("'"+thread.name+"' is still running (timeout in "+str(int(endTime - time.time()))[:4]+" seconds)")
            time.sleep(1.0)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

# Network helper functions
def GetIP():
    import socket
    IP = ''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
        Domoticz.Debug("IP Address is: "+str(IP))
    except Exception as err:
        Domoticz.Debug("GetIP: "+str(err))
    finally:
        s.close()
    return str(IP)

# Configuration Helpers
def getConfigItem(Key=None, Default={}):
    Value = Default
    try:
        Config = Domoticz.Configuration()
        if (Key != None):
            Value = Config[Key] # only return requested key if there was one
        else:
            Value = Config      # return the whole configuration if no key
    except KeyError:
        Value = Default
    except Exception as inst:
        Domoticz.Error("Domoticz.Configuration read failed: '"+str(inst)+"'")
    return Value
    
def setConfigItem(Key=None, Value=None):
    Config = {}
    try:
        Config = Domoticz.Configuration()
        if (Key != None):
            Config[Key] = Value
        else:
            Config = Value  # set whole configuration if no key specified
        Domoticz.Configuration(Config)
    except Exception as inst:
        Domoticz.Error("Domoticz.Configuration operation failed: '"+str(inst)+"'")
    return Config

# Generic helper functions
def stringOrBlank(input):
    if (input == None): return ""
    else: return str(input)

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def DumpHTTPResponseToLog(httpDict):
    if isinstance(httpDict, dict):
        Domoticz.Log("HTTP Details ("+str(len(httpDict))+"):")
        for x in httpDict:
            if isinstance(httpDict[x], dict):
                Domoticz.Log("--->'"+x+" ("+str(len(httpDict[x]))+"):")
                for y in httpDict[x]:
                    Domoticz.Log("------->'" + y + "':'" + str(httpDict[x][y]) + "'")
            else:
                Domoticz.Log("--->'" + x + "':'" + str(httpDict[x]) + "'")

def UpdateDevice(Unit, nValue, sValue, TimedOut):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (str(Devices[Unit].nValue) != str(nValue)) or (str(Devices[Unit].sValue) != str(sValue)) or (str(Devices[Unit].TimedOut) != str(TimedOut)):
            Domoticz.Log("["+Devices[Unit].Name+"] Update "+str(nValue)+"("+str(Devices[Unit].nValue)+"):'"+sValue+"'("+Devices[Unit].sValue+"): "+str(TimedOut)+"("+str(Devices[Unit].TimedOut)+")")
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
    return

def UpdateImage(Unit, Logo):
    if Unit in Devices and Logo in Images:
        if Devices[Unit].Image != Images[Logo].ID:
            Domoticz.Log("Device Image update: 'Chromecast', Currently " + str(Devices[Unit].Image) + ", should be " + str(Images[Logo].ID))
            Devices[Unit].Update(nValue=Devices[Unit].nValue, sValue=str(Devices[Unit].sValue), Image=Images[Logo].ID)
    return
