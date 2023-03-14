import psycopg
from epoch_650 import Epoch_650
from ender5plus import Ender5Plus
import json
import time
import os
import requests

import zipfile


UUT_SELECT_STATEMENT="SELECT ut.id,uut_type_id FROM data.tbl_uut uut LEFT JOIN data.tbl_uut_type ut ON ut.id=uut.uut_type_id WHERE uut.sention_tag=%s;"
SCAN_DEFAULT_SETTING_SELECT_STATEMENT="""
    SELECT scan_setup,scan_info,id
    FROM data.tbl_scan_setup
    WHERE id=(SELECT default_scan_setup_id FROM data.tbl_default_scan_settings WHERE test_element_id=%s AND uut_type_id=%s);"""
TEST_SCAN_SETTING_SELECT_STATEMENT="""
    SELECT ss.scan_setup,ss.scan_info,ts.id 
    FROM data.tbl_test_setup ts LEFT JOIN data.tbl_scan_setup ss ON ss.id=ts.scan_setup_id 
    WHERE test_element_id=%s AND uut_id=%s AND active='T' ORDER BY id DESC LIMIT 1;"""
TEST_SETUP_INSERT_STATEMENT="INSERT INTO data.tbl_test_setup (uut_id,test_element_id,scan_setup_id) VALUES (%s,%s,%s) RETURNING id;"
TEST_INFO_INSERT_STATEMENT="""
    INSERT INTO data.tbl_test_info (id,test_start_time,test_end_time,test_type_id,uut_id,test_info)
    VALUES (%s,to_timestamp(%s),now(),%s,%s,%s);"""


def fetchScanInfo(uutSerial : str, config : json) -> json:
    result = {}

    with psycopg.connect("dbname=sention-systems host={0} port={1} user={2} password={3}".format(
        config['database']['host'],
        config['database']['port'],
        config['database']['username'],
        config['database']['password']
    )) as conn:
        with conn.cursor() as curr:
            
            curr.execute(UUT_SELECT_STATEMENT,[uutSerial])
            res = curr.fetchone()

            if res is not None:
                uut_id = res[0]
                uut_type_id = res[1]

                result['uut_id'] = uut_id

                curr.execute(TEST_SCAN_SETTING_SELECT_STATEMENT,[config['test_element']['id'],uut_id])

                res = curr.fetchone()

                if res is None:
                    curr.execute(SCAN_DEFAULT_SETTING_SELECT_STATEMENT,[config['test_element']['id'],uut_type_id])

                    res = curr.fetchone()

                    if res is None:
                        return None

                    else: 
                        result['scan_setup_id'] = res[2]
                else:
                    result['test_id'] = res[2]

                result['scan_setup'] = res[0]
                result['scan_info'] = res[1]

        return result


def endTest(uutSerial : str, config : json, scanConfig : json, dataPackageFilename : str, testStart : int):

    try:
        with psycopg.connect("dbname=sention-systems host={0} port={1} user={2} password={3}".format(
            config['database']['host'],
            config['database']['port'],
            config['database']['username'],
            config['database']['password']
        )) as conn:
            with conn.cursor() as curr:
                if not 'test_id' in scanConfig:
                    curr.execute(TEST_SETUP_INSERT_STATEMENT,[scanConfig['uut_id'],config['test_element']['id'],scanConfig['scan_setup_id']])
                    res = curr.fetchone()
                    scanConfig['test_id'] = res[0]

                test_info = {}
                test_info['scan_setup'] = scanConfig['scan_setup']
                test_info['scan_info'] = scanConfig['scan_info']

                curr.execute(TEST_INFO_INSERT_STATEMENT,
                                [scanConfig['test_id'],
                                testStart,
                                config['test_element']['test_type'],
                                scanConfig['uut_id'],
                                json.dumps(test_info)]
                                )

                # post data package to API
                files = {'file': open(dataPackageFilename, 'rb')}
                data = {'fileinfo':f'{{"test_id":{scanConfig["test_id"]}}}'}
                getdata = requests.post(config['data_upload_url'], data=data, files=files)
    except:
        print('Did not end test (db upload)')


with open('config.json') as configFile:
    config = json.load(configFile)


cnc = Ender5Plus(config['cnc']['port'])

cnc.homeXYZ()

exit(0)

scanner = Epoch_650(config['device']['port'])
print(scanner.serialNumber)

uutSerial = input('Serial Number : ')
scanConfig = fetchScanInfo(uutSerial, config)

if scanConfig is None:
    exit(1)

scanner.writeSettings(scanConfig['scan_setup']['epoch_650'])

testStart = time.time_ns() // 1000000
outdir = f'/tmp/{testStart}'

os.mkdir(outdir)
filelist = []

scanned = True

for row in range(scanConfig['scan_info']['row_count']):
    for col in range(scanConfig['scan_info']['column_count']):
        input(f'Y:{row} X:{col}')
        if (scanner.scanWav((filename := f'{outdir}/l{row}_{col}.wav'), scanConfig['scan_setup']['epoch_650']['Range'])):
            filelist += [filename]
        else:
            scanned = False

scanner.close()

if not scanned:
    print('Scan not complete')
    exit(1)

with zipfile.ZipFile((filename := outdir.rsplit('/', 1)[1] + '.zip'),"w",compression=zipfile.ZIP_DEFLATED) as newZipFile:
    for f in filelist:
        newZipFile.write(f,os.path.basename(f))

endTest(uutSerial, config, scanConfig, filename, testStart)
