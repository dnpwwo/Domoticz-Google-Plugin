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
<plugin key="GoogleDevs" name="Google Devices - Chromecast and Home" author="dnpwwo" version="1.11.1" wikilink="https://github.com/dnpwwo/Domoticz-Google-Plugin" externallink="https://store.google.com/product/chromecast">
    <description>
        <h2>Domoticz Google Plugin</h2><br/>
        <h3>Key Features</h3>
        <ul style="list-style-type:square">
            <li style="line-height:normal">Devices are discovered automatically and created in the Devices tab</li>
            <li style="line-height:normal">Voice notifications can be sent to selected Google triggered by Domoticz notifications </li>
            <li style="line-height:normal">When network connectivity is lost the Domoticz UI will optionally show the device(s) with Red banner</li>
            <li style="line-height:normal">Device icons are created in Domoticz</li>
            <li style="line-height:normal">Domoticz can control the Application selected</li>
            <li style="line-height:normal">Domoticz can control the Volume including Mute/Unmute</li>
            <li style="line-height:normal">Domoticz can control the playing media.  Play/Pause and skip forward and backwards</li>
            <li style="line-height:normal">Google devices can be the targets of native Domoticz notifications. These are spoken through a chosen device (or audio group) in the language specified in Domoticz </li>
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
            <li style="line-height:normal">Voice message IP address - Required for voice messages, the external address of the Domoticz host</li>
            <li style="line-height:normal">Voice message port - Required for voice messages, the port to use to serve the message to the Google device(s)</li>
            <li style="line-height:normal">Time Out Lost Devices - When true, the devices in Domoitcz will have a red banner when network connectivity is lost</li>
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
        <param field="Address" label="Voice message IP address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Voice message port" width="50px" required="true" default="8009"/>
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
import pychromecast
import pychromecast.config as Consts

DEV_STATUS  = "-1"
DEV_VOLUME  = "-2"
DEV_PLAYING = "-3"
DEV_SOURCE  = "-4"

APP_NONE=0
APP_OTHER=40
Apps={ APP_NONE:{'id':Consts.APP_BACKDROP , 'name':'Backdrop'}, 10:{'id':Consts.APP_SPOTIFY, 'name':'Spotify'}, 20:{'id':'CA5E8412', 'name':'Netflix'}, 30:{'id':Consts.APP_YOUTUBE , 'name':'Youtube'}, APP_OTHER:{'id':'', 'name':'Other'}    }

class GoogleDevice:
    def __init__(self, IP, Port, googleDevice):
        self.Name = googleDevice.device.friendly_name
        self.Model = googleDevice.device.model_name
        self.IP = IP
        self.Port = Port
        self.UUID = str(googleDevice.device.uuid)
        self.GoogleDevice = googleDevice
        self.Ready = False
        self.Active = False
        
        googleDevice.register_status_listener(self.StatusListener(self))
        googleDevice.media_controller.register_status_listener(self.StatusMediaListener(self))
        googleDevice.register_connection_listener(self.ConnectionListener(self))
        googleDevice.socket_client.start()

    class StatusListener:
        def __init__(self, parent):
            self.parent = parent

        def new_cast_status(self, status):
            try:
                self.parent.LogToFile(status)
                self.parent.Ready = True
                self.parent.syncDevices()
            except Exception as err:
                Domoticz.Error("new_cast_status: "+str(err))

    class StatusMediaListener:
        def __init__(self, parent):
            self.parent = parent

        def new_media_status(self, status):
            try:
                self.parent.LogToFile(status)
                self.parent.Ready = True
                self.parent.syncDevices()
            except Exception as err:
                Domoticz.Error("new_media_status: "+str(err))

    class ConnectionListener:
        def __init__(self, parent):
            self.parent = parent

        def new_connection_status(self, new_status):
            try:
                self.parent.LogToFile(new_status)
                Domoticz.Status(self.parent.Name+" is now: "+new_status.status)
                if (new_status.status == "DISCONNECTED") or (new_status.status == "LOST") or (new_status.status == "FAILED"):
                    self.parent.Ready = False
                    self.parent.Active = False
                self.parent.syncDevices()
            except Exception as err:
                Domoticz.Error("new_connection_status: "+str(err))
                Domoticz.Error("new_connection_status: "+str(new_status))

    def LogToFile(self, status):
        if (Parameters["Mode5"] != "False"):
            print(time.strftime('%Y-%m-%d %H:%M:%S')+" ["+self.Name+"] "+str(status), file=open(Parameters["HomeFolder"]+"Messages.log", "a"))
        
    def syncDevices(self):
        global APP_NONE,APP_OTHER
        try:
            # find relevant device
            for Unit in Devices:
                if (Devices[Unit].DeviceID.find(self.UUID) >= 0):
                    nValue = Devices[Unit].nValue
                    sValue = Devices[Unit].sValue
                    self.Active = (not self.GoogleDevice.media_controller.is_idle)
                    if self.Active and (self.GoogleDevice.app_display_name!=None) and (self.GoogleDevice.app_display_name=='Backdrop'): self.Active = False
                    liveStream = "[] "
                    if self.GoogleDevice.media_controller.status.stream_type_is_live: liveStream = "[Live]"
                    if (self.Ready and (self.GoogleDevice.status != None)):
                        if (Devices[Unit].DeviceID[-1] == "1"):     # Overall Status
                            if (not self.Active):
                                nValue = 9
                                sValue = 'Screensaver'
                            elif (self.GoogleDevice.media_controller.status.media_is_generic):
                                nValue = 4
                                sValue = liveStream+str(self.GoogleDevice.media_controller.status.title)
                            elif (self.GoogleDevice.media_controller.status.media_is_tvshow):
                                nValue = 4
                                sValue = liveStream+str(self.GoogleDevice.media_controller.status.series_title)+"[S"+ \
                                            stringOrBlank(self.GoogleDevice.media_controller.status.season)+":E"+ \
                                            stringOrBlank(self.GoogleDevice.media_controller.status.episode)+"] "+\
                                            stringOrBlank(self.GoogleDevice.media_controller.status.title)
                            elif (self.GoogleDevice.media_controller.status.media_is_movie):
                                nValue = 4
                                sValue = liveStream+str(self.GoogleDevice.media_controller.status.title)
                            elif (self.GoogleDevice.media_controller.status.media_is_photo):
                                nValue = 6
                                sValue = str(self.GoogleDevice.media_controller.status.title)
                            elif (self.GoogleDevice.media_controller.status.media_is_musictrack):
                                nValue = 5
                                sValue = liveStream+stringOrBlank(self.GoogleDevice.media_controller.status.artist)+ \
                                            " ("+stringOrBlank(self.GoogleDevice.media_controller.status.album_name)+") "+ \
                                            str(self.GoogleDevice.media_controller.status.title)

                            # Check to see if we are paused
                            if (self.GoogleDevice.media_controller.status.player_is_paused): nValue = 2

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
                            #while (sValue.rfind(")") != -1) and (len(sValue) > 40):
                            #    sValue = sValue.replace(sValue[sValue.rfind("("):sValue.rfind(")")+1],"")
                        elif (Devices[Unit].DeviceID[-1] == "2"):   # Volume
                            nValue = 2
                            if (not self.Active) or (self.GoogleDevice.status.volume_muted == True):
                                nValue = 0
                            sValue = int(self.GoogleDevice.status.volume_level*100)
                        elif (Devices[Unit].DeviceID[-1] == "3"):   # Playing
                            if (self.GoogleDevice.media_controller.status.duration == None):
                                sValue='0'
                            else:
                                try:
                                    sValue=str(int((self.GoogleDevice.media_controller.status.adjusted_current_time / self.GoogleDevice.media_controller.status.duration)*100))
                                except ZeroDivisionError as Err:
                                    sValue="0"
                            if (self.GoogleDevice.media_controller.status.player_is_playing):
                                nValue=2
                                if (sValue=='0'): sValue='1'
                            elif ( self.GoogleDevice.media_controller.status.player_is_paused):
                                nValue=0
                                if (sValue=='0'): sValue='1'
                            else:
                                nValue=0
                                sValue='0'
                        elif (Devices[Unit].DeviceID[-1] == "4"):   # Source (App Name)
                            if (not self.Active):
                                nValue = sValue = APP_NONE
                            else:
                                nValue = sValue = APP_OTHER
                                for App in Apps:
                                    if (Apps[App]['name'] == self.GoogleDevice.app_display_name):
                                        nValue = sValue = App
                                        break
                        else:
                            Domoticz.Error("Unknown device number: "+Devices[Unit].DeviceID)
                            continue
                        UpdateDevice(Unit, nValue, str(sValue), 0)
                    else:
                        if (Parameters["Mode4"] != "False"):
                            UpdateDevice(Unit, Devices[Unit].nValue, Devices[Unit].sValue, 1)
                   
        except RuntimeError: # Suppress error message during start up when dictionary sizes can be changed by discovery thread
            pass
        except Exception as err:
            Domoticz.Error("syncDevices: "+str(err))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            Domoticz.Error(str(exc_type)+", "+fname+", Line: "+str(exc_tb.tb_lineno))

    @property
    def VolumeUnit(self):
        global DEV_VOLUME
        # find first device
        for Unit in Devices:
            if (Devices[Unit].DeviceID == self.UUID+DEV_VOLUME):
                return Unit
        return None

    def __str__(self):
        return "'%s', Model: '%s', UUID: '%s' + IP: '%s:%s'" % (self.Name, self.Model, self.UUID, self.IP, self.Port)

class BasePlugin:
    
    def __init__(self):
        self.googleDevices = {}
        self.stopDiscovery = None
        self.messageServer = None
        self.messageQueue = queue.Queue()
        self.messageThread = threading.Thread(name="GoogleNotify", target=BasePlugin.handleMessage, args=(self,))

    def handleMessage(self):
        Domoticz.Debug("Entering notification handler")
        while True:
            try:
                Message = self.messageQueue.get(block=True)
                if Message is None:
                    self.messageQueue.task_done()
                    break

                Domoticz.Debug("handleMessage: '"+Message["Text"]+"', sent to '"+Message["Target"]+"'")
                if (not os.path.exists(Parameters['HomeFolder']+'Messages')):
                    os.mkdir(Parameters['HomeFolder']+'Messages')
                os.system('curl -s -G "http://translate.google.com/translate_tts" --data "ie=UTF-8&total=1&idx=0&client=tw-ob&&tl='+Parameters["Language"]+'" --data-urlencode "q='+Message["Text"]+'" -A "Mozilla" --compressed -o '+Parameters['HomeFolder']+'Messages/message.mp3')
                
                #import rpdb
                #rpdb.set_trace()
                for uuid in self.googleDevices:
                    if (self.googleDevices[uuid].GoogleDevice.device.friendly_name == Message["Target"]):
                        currentVolume = self.googleDevices[uuid].GoogleDevice.status.volume_level
                        self.googleDevices[uuid].GoogleDevice.quit_app()
                        self.googleDevices[uuid].GoogleDevice.set_volume(int(Parameters["Mode3"]) / 100)
                        self.googleDevices[uuid].GoogleDevice.media_controller.play_media("http://"+Parameters["Address"]+":"+Parameters["Port"]+"/message.mp3", 'music/mp3')
                        abortCounter = 20 # 10 seconds max wait
                        while (self.googleDevices[uuid].GoogleDevice.status.display_name != 'Default Media Receiver') and (abortCounter > 0):
                            Domoticz.Debug("Waiting for 'Default Media Receiver' to start")
                            time.sleep(0.5)
                            abortCounter = abortCounter - 1
                        while (self.googleDevices[uuid].GoogleDevice.status.display_name == 'Default Media Receiver') and (abortCounter > 0):
                            #Domoticz.Debug("Waiting for message to complete playing")
                            time.sleep(0.5)
                            abortCounter = abortCounter - 1
                        self.googleDevices[uuid].GoogleDevice.set_volume(currentVolume)
                        self.googleDevices[uuid].GoogleDevice.quit_app()
                        if (abortCounter > 0):
                            Domoticz.Log("Notification to '"+Message["Text"]+"', sent to '"+Message["Target"]+"' complete")
                        else:
                            Domoticz.Error("Notification '"+Message["Text"]+"', sent to '"+Message["Target"]+"' timed out")
            except Exception as err:
                Domoticz.Error("handleMessage: "+str(err))
            self.messageQueue.task_done()
        Domoticz.Debug("Exiting notification handler")
    
    def discoveryCallback(self, googleDevice):
        global DEV_STATUS,DEV_VOLUME,DEV_PLAYING,DEV_SOURCE
        try:
            uuid = str(googleDevice.device.uuid)
            if (uuid in self.googleDevices):
                Domoticz.Debug("Discovery message seen from known device '"+googleDevice.device.friendly_name+"'")
            else:
                self.googleDevices[uuid] = GoogleDevice(googleDevice.host, googleDevice.port, googleDevice)
                Domoticz.Debug("Discovery message seen from unknown device, added: "+str(self.googleDevices[uuid]))

                createDomoticzDevice = True
                maxUnitNo = 1
                for Device in Devices:
                    if (Devices[Device].Unit > maxUnitNo): maxUnitNo = Devices[Device].Unit
                    if (Devices[Device].DeviceID.find(uuid) >= 0):
                        createDomoticzDevice = False
                        UpdateDevice(Devices[Device].Unit, Devices[Device].nValue, Devices[Device].sValue, 0)

                if (createDomoticzDevice):
                    logoType = Parameters['Key']+'Chromecast'
                    if (googleDevice.device.model_name.find("Home") >= 0) or (googleDevice.device.model_name == "Google Cast Group"): logoType = Parameters['Key']+'HomeMini'
                    Domoticz.Log("Creating devices for '"+googleDevice.device.friendly_name+"' of type '"+googleDevice.device.model_name+"' in Domoticz, look in Devices tab.")
                    Domoticz.Device(Name=self.googleDevices[uuid].Name+" Status", Unit=maxUnitNo+1, Type=17, Switchtype=17, Image=Images[logoType].ID, DeviceID=uuid+DEV_STATUS, Description=googleDevice.device.model_name, Used=0).Create()
                    Domoticz.Device(Name=self.googleDevices[uuid].Name+" Volume", Unit=maxUnitNo+2, Type=244, Subtype=73, Switchtype=7, Image=8, DeviceID=uuid+DEV_VOLUME, Description=googleDevice.device.model_name, Used=0).Create()
                    Domoticz.Device(Name=self.googleDevices[uuid].Name+" Playing", Unit=maxUnitNo+3, Type=244, Subtype=73, Switchtype=7, Image=12, DeviceID=uuid+DEV_PLAYING, Description=googleDevice.device.model_name, Used=0).Create()
                    if (googleDevice.device.model_name.find("Chromecast") >= 0):
                        Options = {"LevelActions": "||||", "LevelNames": "Off|Spotify|Netflix|Youtube|Other", "LevelOffHidden": "false", "SelectorStyle": "0"}
                        Domoticz.Device(Name=self.googleDevices[uuid].Name+" Source",  Unit=maxUnitNo+4, TypeName="Selector Switch", Switchtype=18, Image=12, DeviceID=uuid+DEV_SOURCE, Description=googleDevice.device.model_name, Used=0, Options=Options).Create()
                    elif (googleDevice.device.model_name.find("Google Home") >= 0) or (googleDevice.device.model_name == "Google Cast Group"):
                        pass
                    else:
                        Domoticz.Error("Unsupported device type: "+str(self.googleDevices[uuid]))
                
        except Exception as err:
            Domoticz.Error("discoveryCallback: "+str(err))

    def onStart(self):
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()
            Domoticz.Debug('PyChromeCast Version: '+pychromecast.__version__ )

        #import rpdb
        #rpdb.set_trace()
        Parameters["Mode2"] = json.loads(Parameters["Mode2"].replace('|','"'))
        
        if Parameters['Key']+'Chromecast' not in Images: Domoticz.Image('ChromecastUltra.zip').Create()
        if Parameters['Key']+'HomeMini' not in Images: Domoticz.Image('GoogleHomeMini.zip').Create()
        
        # Mark devices as timed out
        if Parameters["Mode4"] != "False":
            for Device in Devices:
                UpdateDevice(Device, Devices[Device].nValue, Devices[Device].sValue, 1)

        if Parameters["Mode1"] != "":
            Domoticz.Notifier("Google_Devices")

        self.messageServer = Domoticz.Connection(Name="Message Server", Transport="TCP/IP", Protocol="HTTP", Port=Parameters["Port"])
        self.messageServer.Listen()

        # Non-blocking asynchronous discovery, Nice !
        self.stopDiscovery = pychromecast.get_chromecasts(callback=self.discoveryCallback, blocking=False)
        
        self.messageThread.start()

    def onMessage(self, Connection, Data):
        try:
            Domoticz.Debug("onMessage called from: "+Connection.Address+":"+Connection.Port)

            if (not 'URL' in Data):
                Domoticz.Error("Invalid we request received, no URL present")
                DumpHTTPResponseToLog(Data)
                return

            with open(Parameters["HomeFolder"]+"Messages"+Data["URL"], mode='rb') as file:
                fileContent = file.read()
            Domoticz.Debug("Read "+str(len(fileContent))+" bytes of data into variable of type: "+str(type(fileContent)))

            Connection.Send({"Status":"200 OK", "Headers": {"Content-Type": "music/mp3"}, "Data": fileContent})

        except Exception as inst:
            Domoticz.Error("Exception detail: '"+str(inst)+"'")
            DumpHTTPResponseToLog(Data)
            raise

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
                    if (Apps[Level]['id']!=''):
                        self.googleDevices[uuid].GoogleDevice.start_app(Apps[Level]['id'])
                    else:
                        self.googleDevices[uuid].GoogleDevice.start_app(Apps[40]['id'])
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
            if (self.googleDevices[uuid].GoogleDevice.app_display_name != Apps[APP_NONE]['name']) and (self.googleDevices[uuid].GoogleDevice.app_display_name != Parameters["Mode2"]["Video"]):
                self.googleDevices[uuid].GoogleDevice.quit_app()
                for App in Apps:
                    if (Apps[App]['name'] == Parameters["Mode2"]["Video"]):
                        self.googleDevices[uuid].GoogleDevice.start_app(Apps[App]['id'])
                        break
        elif (action == 'Audio'): # Blockly command
            if (self.googleDevices[uuid].GoogleDevice.app_display_name != Apps[APP_NONE]['name']) and (self.googleDevices[uuid].GoogleDevice.app_display_name != Parameters["Mode2"]["Audio"]):
                self.googleDevices[uuid].GoogleDevice.quit_app()
                for App in Apps:
                    if (Apps[App]['name'] == Parameters["Mode2"]["Audio"]):
                        self.googleDevices[uuid].GoogleDevice.start_app(Apps[App]['id'])
                        break
        elif (action == 'Sendnotification'):
            self.messageQueue.put({"Target":self.googleDevices[uuid].GoogleDevice.device.friendly_name, "Text":params})
        elif (action == 'Quit'):
            self.googleDevices[uuid].GoogleDevice.quit_app()

    def onHeartbeat(self):
        for uuid in self.googleDevices:
            if (self.googleDevices[uuid].Active):
                self.googleDevices[uuid].syncDevices()

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("onNotification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)
        self.messageQueue.put({"Target":Parameters['Mode1'], "Text":Text})

    def onStop(self):
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
        while (threading.active_count() > 1):
            for thread in threading.enumerate():
                if (thread.name != threading.current_thread().name):
                    Domoticz.Log("'"+thread.name+"' is still running, waiting otherwise Domoticz will crash on plugin exit.")
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

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

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
