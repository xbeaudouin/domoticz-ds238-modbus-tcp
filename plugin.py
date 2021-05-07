#!/usr/bin/env python
"""
Hiking DDS238-2 ZN/S Energy Meter
Author: Xavier Beaudouin
Requirements: 
    1. modbus over TCP adapter like PW21
    2. pymodbus AND pymodbusTCP
"""
"""
<plugin key="DS238_ModbusTCP" name="DS238-2 ZN/S ModbusTCP" author="Xavier Beaudouin" version="0.0.1" externallink="https://github.com/xbeaudouin/domoticz-ds238-modbus-tcp">
    <params>
        <param field="Address" label="IP Address" width="150px" required="true" />
        <param field="Port" label="Port Number" width="100px" required="true" default="502" />
        <param field="Mode3" label="Modbus address" width="100px" required="true" default="1" />
        <param field="Mode6" label="Debug" width="100px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true" />
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import sys

sys.path.append('/usr/local/lib/python3.4/dist-packages')
sys.path.append('/usr/local/lib/python3.5/dist-packages')
sys.path.append('/usr/local/lib/python3.6/dist-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/local/lib/python3.8/dist-packages')

import pymodbus

from pyModbusTCP.client import ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload   import BinaryPayloadDecoder

class BasePlugin:
    #enabled = False
    def __init__(self):
        return

    def onStart(self):
        try:
            Domoticz.Log("DS238-2 ZN/S Energy Meter TCP loaded!, using python v" + sys.version[:6] + " and pymodbus v" + pymodbus.__version__)
        except:
            Domoticz.Log("DS238-2 ZN/S Energy Meter TCP loaded!")

        # Check dependancies
        try:
            if (float(Parameters["DomoticzVersion"][:6]) < float("2020.2")): Domoticz.Error("WARNING: Domoticz version is outdated or not supported. Please update!")
            if (float(sys.version[:1]) < 3): Domoticz.Error("WARNING: Python3 should be used !")
            if (float(pymodbus.__version__[:3]) < float("2.3")): Domoticz.Error("WARNING: pymodbus version is outdated, please update!")
        except:
            Domoticz.Error("Warning ! Dependancies could not be checked !")

        # Parse parameters
        
        # Debug
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
        else:
            Domoticz.Debugging(0)

        self.IPAddress = Parameters["Address"]
        self.IPPort    = Parameters["Port"]
        self.MBAddr    = int(Parameters["Mode3"])

        Domoticz.Debug("Query IP " + self.IPAddress + ":" + str(self.IPPort) +" on device : "+str(self.MBAddr))

        # Create the devices if they does not exists
        if 1 not in Devices:
            #Domoticz.Device(Name="Total Energy",   Unit=1, Type=0x71, Subtype=0x0, Used=0).Create()
            Domoticz.Device(Name="Total Energy",   Unit=1, Type=248, Subtype=33, Used=0).Create()
        if 2 not in Devices:
            #Domoticz.Device(Name="Export Energy",  Unit=2, Type=0x71, Subtype=0x0, Used=0).Create()
            Domoticz.Device(Name="Export Energy",  Unit=2, Type=248, Subtype=33, Used=0).Create()
        if 3 not in Devices:
            #Domoticz.Device(Name="Import Energy",  Unit=3, Type=0x71, Subtype=0x0, Used=0).Create()
            Domoticz.Device(Name="Import Energy",  Unit=3, Type=248, Subtype=33, Used=0).Create()
        if 4 not in Devices:
            Domoticz.Device(Name="Voltage",        Unit=4, TypeName="Voltage", Used=0).Create()
        if 5 not in Devices:
            Domoticz.Device(Name="Current",        Unit=5, TypeName="Current (Single)", Used=0).Create()
        if 6 not in Devices:
            Options = { "Custom": "1;W" }
            Domoticz.Device(Name="Active Power",   Unit=6, TypeName="Custom", Used=0, Options=Options).Create()
        if 7 not in Devices:
            Options = { "Custom": "1;VAr" }
            Domoticz.Device(Name="Reactive Power", Unit=7, TypeName="Custom", Used=0, Options=Options).Create()
        if 8 not in Devices:
            Options = { "Custom": "1;PF" }
            Domoticz.Device(Name="Power Factor",   Unit=8, TypeName="Custom", Used=0, Options=Options).Create()
        if 9 not in Devices:
            Options = { "Custom": "1;Hz" }
            Domoticz.Device(Name="Frequency",      Unit=9, TypeName="Custom", Used=0, Options=Options).Create()

        return


    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")
        return

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug(" Interface : IP="+self.IPAddress +", Port="+str(self.IPPort)+" ID="+str(self.MBAddr))
        try:
            client = ModbusClient(host=self.IPAddress, port=self.IPPort, unit_id=self.MBAddr, auto_open=True, auto_close=True, timeout=2)
        except:
            Domoticz.Error("Error connecting to TCP/Interface on address : "+self.IPaddress+":"+str(self.IPPort))
            # Set value to 0 -> Error on all devices
            Devices[1].Update(1, "0")
            Devices[2].Update(1, "0")
            Devices[3].Update(1, "0")
            Devices[4].Update(1, "0")
            Devices[5].Update(1, "0")
            Devices[6].Update(1, "0")
            Devices[7].Update(1, "0")
            Devices[8].Update(1, "0")
            Devices[9].Update(1, "0")

        # Total Energy
        data = client.read_holding_registers(0, 2)
        Domoticz.Debug("Data from register 0: "+str(data))
        # Unsigned 32 
        decoder = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.Big, wordorder=Endian.Big)
        # Value
        value = decoder.decode_32bit_int()
        # Scale factor / 100
        value = str ( round (value / 100, 3))
        Domoticz.Debug("Value after conversion : "+str(value))
        Devices[1].Update(1, value)

        # Export Energy
        data = client.read_holding_registers(0x8, 2)
        Domoticz.Debug("Data from register 0x8: "+str(data))
        # Unsigned 32 
        decoder = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.Big, wordorder=Endian.Big)
        # Value
        value = decoder.decode_32bit_int()
        # Scale factor / 100
        value = str ( round (value / 100, 3))
        Domoticz.Debug("Value after conversion : "+str(value))
        Devices[2].Update(1, value)

        # Import Energy
        data = client.read_holding_registers(0xA, 2)
        Domoticz.Debug("Data from register 0xA: "+str(data))
        # Unsigned 32 
        decoder = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.Big, wordorder=Endian.Big)
        # Value
        value = decoder.decode_32bit_int()
        # Scale factor / 100
        value = str ( round (value / 100, 3))
        Domoticz.Debug("Value after conversion : "+str(value))
        Devices[3].Update(1, value)

        # Voltage
        data = client.read_holding_registers(0xC, 1)
        Domoticz.Debug("Data from register 0xC: "+str(data))
        # Unsigned 16
        decoder = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.Big, wordorder=Endian.Big)
        # Value
        value = decoder.decode_16bit_int()
        # Scale factor / 10
        value = str ( round (value / 10, 3))
        Domoticz.Debug("Value after conversion : "+str(value))
        Devices[4].Update(1, value)

        # Current
        data = client.read_holding_registers(0xD, 1)
        Domoticz.Debug("Data from register 0xD: "+str(data))
        # Unsigned 16
        decoder = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.Big, wordorder=Endian.Big)
        # Value
        value = decoder.decode_16bit_int()
        # Scale factor / 100
        value = str ( round (value / 100, 3))
        Domoticz.Debug("Value after conversion : "+str(value))
        Devices[5].Update(1, value)

        # Active Power
        data = client.read_holding_registers(0xE, 1)
        Domoticz.Debug("Data from register 0xE: "+str(data))
        # Unsigned 16
        decoder = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.Big, wordorder=Endian.Big)
        # Value
        value = decoder.decode_16bit_int()
        # Scale factor / 100
        #value = str ( round (value / 100, 3))
        Domoticz.Debug("Value after conversion : "+str(value))
        Devices[6].Update(1, str(value))

        # Reactive Power
        data = client.read_holding_registers(0xF, 1)
        Domoticz.Debug("Data from register 0xF: "+str(data))
        # Unsigned 16
        decoder = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.Big, wordorder=Endian.Big)
        # Value
        value = decoder.decode_16bit_int()
        # Scale factor / 100
        #value = str ( round (value / 100, 3))
        Domoticz.Debug("Value after conversion : "+str(value))
        Devices[7].Update(1, str(value))

        # Power Factor
        data = client.read_holding_registers(0x10, 1)
        Domoticz.Debug("Data from register 0x10: "+str(data))
        # Unsigned 16
        decoder = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.Big, wordorder=Endian.Big)
        # Value
        value = decoder.decode_16bit_int()
        # Scale factor / 1000
        value = str ( round (value / 1000, 3))
        Domoticz.Debug("Value after conversion : "+str(value))
        Devices[8].Update(1, value)

        # Frequency
        data = client.read_holding_registers(0x11, 1)
        Domoticz.Debug("Data from register 0x11: "+str(data))
        # Unsigned 16
        decoder = BinaryPayloadDecoder.fromRegisters(data, byteorder=Endian.Big, wordorder=Endian.Big)
        # Value
        value = decoder.decode_16bit_int()
        # Scale factor / 100
        value = str ( round (value / 100, 3))
        Domoticz.Debug("Value after conversion : "+str(value))
        Devices[9].Update(1, value)



global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
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
