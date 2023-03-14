from ender5plus import Ender5Plus
import json

with open('config.json') as configFile:
    config = json.load(configFile)

cnc = Ender5Plus(config['cnc'])

cnc.homeXYZ()

cnc.measureZ([], 10)

exit(0)
