import psycopg
from epoch_650 import Epoch_650
import json
import time
import os


UUT_SELECT_STATEMENT="SELECT uut_id,uut_type_id FROM data.tbl_uut uut LEFT JOIN data.tbl_uut_type ut ON ut.id=uut.uut_type_id WHERE uut.sention_tag=%s;"
SCAN_DEFAULT_SETTING_SELECT_STATEMENT="""
    SELECT scan_setup,scan_info
    FROM data.tbl_scan_setup
    WHERE id=(SELECT default_scan_setup_id FROM data.tbl_default_scan_settings WHERE test_element_id=%s AND uut_type_id=%s);"""
TEST_SCAN_SETTING_SELECT_STATEMENT="""
    SELECT ss.scan_setup,ss.scan_info,ts.id 
    FROM data.tbl_test_setup ts LEFT JOIN data.tbl_scan_setup ss ON ss.id=ts.scan_setup_id 
    WHERE test_element_id=%s AND uut_id=%s AND active='T' ORDER BY id DESC LIMIT 1;"""
TEST_SETUP_INSERT_STATEMENT="INSERT INTO data.tbl_test_setup (uut_id,test_element_id,scan_setup_id) VALUES (%s,%s,%s) RETURNING id;"


def fetchScanInfo(uutSerial : str, config : json) -> json:
    result = {}

    with psycopg.connect("dbname=sention-systems host={0} port={1} user={2} password={3}".format(
        config['database']['host'],
        config['database']['port'],
        config['database']['username'],
        config['database']['password']
    )) as conn:
        with conn.cursor() as curr:
            
            curr.execute(UUT_SELECT_STATEMENT, uutSerial)
            res = curr.fetchone()

            if res is not None:
                uut_id = res[0]
                uut_type_id = res[1]

                curr.execute(TEST_SCAN_SETTING_SELECT_STATEMENT, [config['test_element']['id'],uut_id])

                res = curr.fetchone()

                if res is None:
                    res = curr.execute(SCAN_DEFAULT_SETTING_SELECT_STATEMENT,[config['test_element']['id'],uut_type_id])
                    curr.execute(query)

        return res[0]


with open('config.json') as configFile:
    config = json.load(configFile)

scanner = Epoch_650(config['device']['port'])
print(scanner.serialNumber)

uutSerial = input('Serial Number : ')
scanConfig = fetchScanInfo(uutSerial, config)

outdir = '/tmp/' + str(time.time_ns() // 1000000)

os.mkdir(outdir)

for row in range(scanConfig['rhoddenbox_1_0']['scan']['row_count']):
    for col in range(scanConfig['rhoddenbox_1_0']['scan']['column_count']):
        input(f'Y:{row} X:{col}')
        scanner.scanWav(f'{outdir}/l{row}_{col}.wav', scanConfig['rhoddenbox_1_0']['epoch_6xx']['Range'])

scanner.close()