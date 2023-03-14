import serial
import json


class Ender5Plus:

    def __init__(self, config : dict):

        self._device = serial.Serial(config['port'], config['baud'], timeout=10)
        self._config = config

        while (reply := self._device.readline()) != b'':
            print(reply)
            if reply == b'===Initing RTS has finished===\n':
                self._device.readline()
                return


    def homeXYZ(self) -> bool:

        self._transact('G90\n','ok')
        self._transact(f'G01 Z{self._config["head_z_pos"]}\n','ok')
        self._transact('G28\n','X:')


    def measureZ(self, points, cellHeight):

        cellHeightCleared = cellHeight + 10

        self._transact('G90\n','ok')
        self._transact(f'G01 Z{cellHeightCleared}\n','ok')
        self._transact(f'G01 X349 Y293\n','ok')
        self._transact('G91\n','ok')
        self._transact('G01 X-10 Y-10 Z0\n','ok')
        self._transact('G30\n','Bed')
        self._transact('G01 X-25 Y Z0\n','ok')
        self._transact('G30\n','Bed')
        self._transact('G01 X0 Y-105 Z0\n','ok')
        self._transact('G30\n','Bed')
        self._transact('G01 X25 Y0 Z0\n','ok')
        self._transact('G30\n','Bed')
        self._transact('G90\n','ok')
        self._transact(f'G01 X349 Y293\n','ok')


    def _transact(self, command : str, reply : str) -> str:

        self._device.write(command.encode())

        print(command)

        while (cncreply := self._device.readline()) != b'':
            print(cncreply)
            if cncreply[:len(reply)] == reply.encode():
                return cncreply.decode('utf-8')

        return cncreply.decode('utf-8')