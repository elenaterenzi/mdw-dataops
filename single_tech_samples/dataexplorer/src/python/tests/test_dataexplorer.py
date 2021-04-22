# Test ADX Insert

import os
import sys
import argparse
import json
from datetime import timedelta

from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.mgmt.kusto.models import ReadWriteDatabase
from azure.mgmt.kusto import KustoManagementClient
from azure.common.credentials import ServicePrincipalCredentials

import sys # added!
sys.path.append("..") # added!
import dataexplorerutil


def inc(x):
    return x +1
 
def test_answer():
    assert inc(4) ==5

def test_answer2():
    assert inc(4)== 5
    #assert 4 == 5

def test_insert_data():
    RETENTION_DAYS = os.getenv('RETENTION_DAYS', "No Env Setting")
    print(RETENTION_DAYS)
    assert RETENTION_DAYS=='100'
    adxHelper=dataexplorerutil.ADXHelper()
    adxHelper.init_config()
    adxHelper.initialize_kusto_client()

    databasename="dataopsdb-0"
    tablename="CO2"
    flush_immediately=True
    adxHelper.insert_data(databasename,tablename,"./testdata/testdata01.json","", flush_immediately)
    #adxHelper.insert_data("","","","")



 
 
 
 
 