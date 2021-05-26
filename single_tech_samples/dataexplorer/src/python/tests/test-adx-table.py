import os, sys, time
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

def test_insert_data():
    RETENTION_DAYS = os.getenv('RETENTION_DAYS', "No Env Setting")
    print(RETENTION_DAYS)
    assert RETENTION_DAYS=='100'
    adxHelper=dataexplorerutil.ADXHelper()
    adxHelper.init_config()
    adxHelper.initialize_kusto_client()

    databasename="dataopsdb-0"
    tablename="CO2"
    sourcefilelocation="./testdata/testdata01.json"
    insert_data_validate(databasename,tablename,sourcefilelocation)


def insert_data_validate(databasename,tablename,sourcefilelocation):
    adxHelper=dataexplorerutil.ADXHelper()
    adxHelper.init_config()
    adxHelper.initialize_kusto_client()

    databasename=databasename
    tablename=tablename
    kql="{} | count".format(tablename)
    is_print_result=True
    print ("database name : {} ,  table name {} ".format(databasename,tablename))

    result=adxHelper.run_kql_query(databasename,kql,is_print_result)
    
    totalrecord=result[0][0]
    print ("First column of  query result is: {} ".format(totalrecord))
  

    adxHelper.insert_data(databasename,tablename,sourcefilelocation,"", True)
    #self.insert_data("","","","")

    print ("Waiting 15 seconds for ADX to ingest data before validating the result")
    time.sleep(15)
    new_result=adxHelper.run_kql_query(databasename,kql,is_print_result)

    new_totalrecord=new_result[0][0]
    print ("First column of  query result is: {} ".format(new_totalrecord))
    assert(new_totalrecord==totalrecord+1)


if __name__ == "__main__": 
    # Get related arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--databasename',  help='Database Name', type=str)
    parser.add_argument('-t', '--tablename',  help='Table Name', type=str)
    parser.add_argument('-s', '--sourcefilelocation',  help='JSON File location for testing', type=str)
    args = parser.parse_args()
    print ("Run insert data validation")
    insert_data_validate(args.databasename,args.tablename,args.sourcefilelocation)