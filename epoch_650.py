import serial
from io import StringIO
import numpy as np
from scipy.io import wavfile
import json


class Epoch_650:

    def __init__(self, portname : str):
        self._data = []
        self.device = serial.Serial(portname, 115200, timeout=5)

        try:
            while len(self.device.readline()) > 0:
                pass
        except:
            pass

        self.device.write(b'param_SNo?\r\n')
        self.serialNumber = self.device.readline().decode('utf-8')[:-2]
        
        # Read out the OK
        self.device.readline()


    def writeSettings(self, settings : json):

        for key in settings:
            print(f'param_{key}={settings[key]}')
            self.device.write(bytes(f'param_{key}={settings[key]}\r\n','utf-8'))

            # Read out the OK
            self.device.readline()


    def addScan(self, filename='/tmp/scanData.csv'):
        self.device.write(b'param_RawData=0,120\r\n')
        with open(filename,'wb') as dataFile:
            dataFile.write(self.device.readline())
        
        # Read out the OK
        self.device.readline()


    def scanWav(self, filename, sampleWindow) -> bool:
        self.device.write(bytes(f'param_RawData=0,{sampleWindow}\r\n','utf-8'))
        npData = np.loadtxt(StringIO(self.device.readline()[:-2].decode('utf-8')), delimiter=',') - 256

        print("Samples : {0}", len(npData))

        scaled = np.int16(npData / np.max(np.abs(npData)) * 32767)

        wavfile.write(filename, len(scaled), scaled)

        # Read out the OK
        self.device.readline()

        return True


    def close(self):
        self.device.close()

