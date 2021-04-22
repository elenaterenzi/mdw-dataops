"""
  [Microsoft Azure Data Explorer Helper]
  The code is based on Azure Date Explorer(ADX) python SDK. 
  It simplied ADX database/table operations by automatically generate operation commands based on pre-defined schema. 
"""
import os
import sys
import argparse
import json
from datetime import timedelta

from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.mgmt.kusto.models import ReadWriteDatabase
from azure.mgmt.kusto import KustoManagementClient
from azure.common.credentials import ServicePrincipalCredentials
from azure.kusto.ingest import (
    QueuedIngestClient,
    IngestionProperties,
    FileDescriptor,
    BlobDescriptor,
    StreamDescriptor,
    DataFormat,
    ReportLevel,
    IngestionMappingType,
    KustoStreamingIngestClient,
)

class ADXHelper:

    RETENTION_DAYS =100
    KUSTO_MGMT_CLIENT = None
    SERVICE_CLIENT = None
    QUEUEDINGESTCLIENT=None 

    CLUSTER = None
    CLUSTER_NAME = None
    RESOURCE_GROUP = None

    CLIENT_ID = None
    CLIENT_SECRET = None
    TENANT_ID = None
    SUBSCRIPTION_ID = None
    REGION = None

    MAX_BATCHTIME = "00:01:00"
    MAX_ITEMS = "500"
    MAX_RAWSIZE = "1024"
    SOFTDELETEPERIOD = "3650"
    HOTCACHEPERIOD = "3650"
    DATABASE_NAME_FORMAT = "dataopsdb-{INDEX}"
    TABLE_LIST_STR = "CO2,TEMP"
    TABLE_LIST = ["CO2", "TEMP"]
    BATCH_INGESTION_POLICY = """
    {{
        "MaximumBatchingTimeSpan":"{MAX_BATCHTIME}",
        "MaximumNumberOfItems":{MAX_ITEMS},
        "MaximumRawDataSizeMB":{MAX_RAWSIZE}
    }}
    """

    def __init__(self):
        self.init_config()

    def init_config(self):
        """get config from environment
        """
        #global RETENTION_DAYS, RESOURCE_GROUP, CLUSTER_NAME
        #global REGION, CLUSTER, CLIENT_ID, CLIENT_SECRET, TENANT_ID, SUBSCRIPTION_ID
        #global MAX_BATCHTIME, MAX_ITEMS, MAX_RAWSIZE
        #global SOFTDELETEPERIOD, HOTCACHEPERIOD
        #global TABLE_LIST_STR, TABLE_LIST
        ADXHelper.RETENTION_DAYS = os.getenv('RETENTION_DAYS', ADXHelper.RETENTION_DAYS)
        ADXHelper.RESOURCE_GROUP = os.getenv('RESOURCE_GROUP')
        ADXHelper.REGION = os.getenv('REGION')
        ADXHelper.CLIENT_ID = os.getenv('CLIENT_ID')
        ADXHelper.CLIENT_SECRET = os.getenv('CLIENT_SECRET')
        ADXHelper.TENANT_ID = os.getenv('TENANT_ID')
        ADXHelper.SUBSCRIPTION_ID = os.getenv('SUBSCRIPTION_ID')
        ADXHelper.CLUSTER_NAME = os.getenv('CLUSTER_NAME')
        ADXHelper.MAX_BATCHTIME = os.getenv('MAX_BATCHTIME', ADXHelper.MAX_BATCHTIME)
        ADXHelper.MAX_ITEMS = int(os.getenv('MAX_ITEMS', ADXHelper.MAX_ITEMS))
        ADXHelper.MAX_RAWSIZE = int(os.getenv('MAX_RAWSIZE', ADXHelper.MAX_RAWSIZE))
        ADXHelper.SOFTDELETEPERIOD = int(os.getenv('SOFTDELETEPERIOD', ADXHelper.SOFTDELETEPERIOD))
        ADXHelper.HOTCACHEPERIOD = int(os.getenv('HOTCACHEPERIOD', ADXHelper.HOTCACHEPERIOD))
        ADXHelper.DATA_CLUSTER = f"https://{ADXHelper.CLUSTER_NAME}.{ADXHelper.REGION}.kusto.windows.net"
        ADXHelper.INGEST_CLUSTER = f"https://ingest-{ADXHelper.CLUSTER_NAME}.{ADXHelper.REGION}.kusto.windows.net"
        ADXHelper.TABLE_LIST_STR =  os.getenv('TABLE_LIST_STR', ADXHelper.TABLE_LIST_STR)
        ADXHelper.TABLE_LIST = ADXHelper.TABLE_LIST_STR.split(',')
 
    def initialize_kusto_client(self):
        """initialize kusto client
        """
        try:
            #global SERVICE_CLIENT, KUSTO_MGMT_CLIENT, QUEUEDINGESTCLIENT

            credentials = ServicePrincipalCredentials(
                client_id=ADXHelper.CLIENT_ID,
                secret=ADXHelper.CLIENT_SECRET,
                tenant=ADXHelper.TENANT_ID
            )

            ADXHelper.KUSTO_MGMT_CLIENT = KustoManagementClient(credentials, ADXHelper.SUBSCRIPTION_ID)
            data_kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                ADXHelper.DATA_CLUSTER,
                ADXHelper.CLIENT_ID,
                ADXHelper.CLIENT_SECRET,
                ADXHelper.TENANT_ID)
            ADXHelper.SERVICE_CLIENT = KustoClient(data_kcsb)

            ingest_kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                ADXHelper.INGEST_CLUSTER,
                ADXHelper.CLIENT_ID,
                ADXHelper.CLIENT_SECRET,
                ADXHelper.TENANT_ID)
            ADXHelper.QUEUEDINGESTCLIENT=QueuedIngestClient(ingest_kcsb)

        except Exception as err:
            print("error for KustoClient")
            print(err)
            raise


    def get_ingest_mapping(self,file_path):
        """get ingestion mapping from schema
        :param fp: schemaFp
        :type fp: string
        """
        mapping = ["'['"]
        with open(file_path, 'r', encoding='utf-8') as mapping_fd:
            content = json.load(mapping_fd)
            line_count = len(content['schema'])
            for i in range(line_count):
                field = content['schema'][i]
                kql_dict = {"column": '{field}'.format(field=field['field']),
                            "datatype": '{adxType}'.format(adxType=field['adxType']),
                            "Properties": {"Path": '$.{field}'.format(field=field['field'])}}

                if 'ingest' in field.get('properties', {}):
                    source = field['properties']['ingest']['source']
                    transform = field['properties']['ingest']['transform']
                    kql_dict["Properties"] = {"Path": '$.{source}'.format(source=source), \
                    "transform": transform}

                if i != line_count - 1:
                    json_str = '\'{json_kql},\''.format(json_kql=json.dumps(kql_dict))
                else:
                    json_str = '\'{json_kql}\''.format(json_kql=json.dumps(kql_dict))

                mapping.append(json_str)

        mapping.append("']'")
        return '\n'.join(mapping)


    def get_schema(self,file_path, get_raw=True):
        """get schema
        :param file_path: schema file path
        :type file_path: string
        :param get_raw: [description], defaults to True
        :type get_raw: bool, optional
        :return: schema json content
        :rtype: dict
        """
        schema = {}
        with open(file_path, 'r', encoding='utf-8') as schema_fd:
            content = json.load(schema_fd)
            for field in content["schema"]:
                fieldname = field["field"]
                adx_type = field["adxType"]
                is_raw = True
                if "update" in field.get("properties", {}):
                    is_raw = False

                if (get_raw and is_raw) or (not get_raw):
                    schema[fieldname] = adx_type
        return schema

    def create_table_command(self,table, schema):
        """get a query that will create table
        :param table: table name
        :type table: string
        :param schema: schema dict
        :type schema: json
        """

        schema_str = ", ".join(["%s:%s" % (k, schema[k]) for k in sorted(list(schema.keys()))])
        command = '.create-merge table %s (%s)' % (table, schema_str)
        return command

    def retention_policy(self,table):
        """retention_policy
        :param table: table name
        :type table: string
        """
        command = ".alter-merge table %s policy retention softdelete = %sd \
        recoverability = disabled" % (table, RETENTION_DAYS)
        return command

    def ingestion_mapping_command(self,table, schema_file):
        """ingestion_mapping_command
        :param table: table name
        :type table: string
        """
        #TODO:Change mapping name to variable#TODO:Change mapping name to env variable
        #TODO:Need to align with function setting
        command = '.create-or-alter table %s ingestion json mapping "json_mapping_01"\n%s' \
        % (table, get_ingest_mapping(schema_file))
        return command

    def batch_policy(self,database):
        """retention_policy
        :param table: table name
        :type table: string
        """
        ingestion_policy_json = BATCH_INGESTION_POLICY.format(MAX_BATCHTIME=MAX_BATCHTIME, \
            MAX_ITEMS=MAX_ITEMS, \
            MAX_RAWSIZE=MAX_RAWSIZE)
        ingestion_policy = json.dumps(json.loads(ingestion_policy_json))

        command = ".alter database [%s] policy ingestionbatching @'%s'"%(database, ingestion_policy)
        return command


    def drop_entity_command(self,entity_type, entity_value):
        """drop entity

        :param entity_type: entity type
        :type entity_type: string. ex table, database
        :param entity_value: entity value. ex: database name
        :type entity_value: string
        :return: kql command string
        :rtype: string
        """
        return '.drop %s %s ifexists' % (entity_type, entity_value)



    def create_database(self,number_of_companies):
        """create_database
        :param number_of_companies: number_of_companies
        :type number_of_companies: int
        """
        soft_deleteperiod = timedelta(days=SOFTDELETEPERIOD)
        hot_cacheperiod = timedelta(days=HOTCACHEPERIOD)
        database_operations = KUSTO_MGMT_CLIENT.databases
        for index in range(0, number_of_companies):
            try:
                database_name = DATABASE_NAME_FORMAT.format(INDEX=index)
                _database = ReadWriteDatabase(location=REGION, soft_delete_period=soft_deleteperiod, \
                    hot_cache_period=hot_cacheperiod)
                print(f"Create Database {index} - {database_name}")
                database_operations.create_or_update(resource_group_name=RESOURCE_GROUP, \
                    cluster_name=CLUSTER_NAME, database_name=database_name, parameters=_database)
            except Exception as err:
                print(err)
                raise

    def update_retention_date(self,number_of_companies):
        """update table retention date
        :param number_of_companies: number_of_companies
        :type number_of_companies: int
        """
        print("update retention date")
        for index in range(0, number_of_companies):
            database_name = DATABASE_NAME_FORMAT.format(INDEX=index)
            print(f"Update retention date Policy for Database {index} - {database_name}")
            command_list = []
            for table_name in TABLE_LIST:
                command_list.append(retention_policy(table_name))
            try:
                for command in command_list:
                    SERVICE_CLIENT.execute(database_name, command)
            except Exception as err:
                print(err)
                raise

    def update_ingestion_policy(self,number_of_companies):
        """update ingestion policy

        :param number_of_companies: number_of_companies
        :type number_of_companies: int
        """
        print("update_ingestion_policy")
        for index in range(0, number_of_companies):
            database_name = DATABASE_NAME_FORMAT.format(INDEX=index)
            print(f"Update Ingestion Policy for Database {index} - {database_name}")
            command = batch_policy(database_name)
            print(f"Batch Policy Command:{command}")
            try:
                SERVICE_CLIENT.execute_mgmt(database_name, command)
            except Exception as err:
                print(err)
                raise


    def create_table_of_database(self,number_of_companies, schema_file):
        """create table for existing database

        :param number_of_companies: number_of_companies
        :type number_of_companies: int
        :param schema_file: schema file
        :type schema_file: json
        """
        for index in range(0, number_of_companies):
            database_name = DATABASE_NAME_FORMAT.format(INDEX=index)
            print(f"Create Table for Database {index} - {database_name}")
            #add_userrole(database_name)
            command_list = create_tables_command(schema_file)
            try:
                for command in command_list:
                    #while True:
                    SERVICE_CLIENT.execute(database_name, command)
            except Exception as err:
                print(err)
                raise


    def delete_database(self,number_of_companies):
        """deletedatabase

    :param number_of_companies: number_of_companies
        :type number_of_companies: int
        """
        soft_deleteperiod = timedelta(days=ADXHelper.SOFTDELETEPERIOD)
        hot_cacheperiod = timedelta(days=ADXHelper.HOTCACHEPERIOD)
        for index in range(0, number_of_companies):
            try:
                database_name = DATABASE_NAME_FORMAT.format(INDEX=index)
                print(f"Delete Database {index} - {database_name}")
                database_operations = KUSTO_MGMT_CLIENT.databases
                _database = ReadWriteDatabase(location=REGION, soft_delete_period=soft_deleteperiod, \
                hot_cache_period=hot_cacheperiod)
                database_operations.delete(resource_group_name=RESOURCE_GROUP, \
                    cluster_name=CLUSTER_NAME, database_name=database_name, \
                    parameters=_database)
            except Exception as err:
                print(err)
                raise

    def create_tables_command(self,schema_file):
        """create one table for existing database

        :param number_of_companies: number_of_companies
        :type number_of_companies: int
        :param schema_file: schema file
        :type schema_file: json
        """
        command_list = []
        for table_name in TABLE_LIST:
            schema = get_schema(schema_file, False)
            command_list.append(create_table_command(table_name, schema))
            command_list.append(retention_policy(table_name))
            command_list.append(ingestion_mapping_command(table_name, schema_file))
        return command_list

    def run_adx_csl_command(self,file_path,number_of_companies):
        """run adx script
        :param file_path: schema file path
        :type file_path: string
        :param number_of_companies: number_of_companies
        :type number_of_companies: int
        """
        print("Run ADX Script")
        with open(file_path, 'r', encoding='utf-8') as csl_file:
            csl_command=csl_file.read()

        for index in range(0, number_of_companies):
            database_name = DATABASE_NAME_FORMAT.format(INDEX=index)
            print(f"Update Ingestion Policy for Database {index} - {database_name}")
            try:
                SERVICE_CLIENT.execute_mgmt(database_name, csl_command)
            except Exception as err:
                print(err)
                raise

    def insert_data(self,database_name,table_name, data_file_path, data_format, flush_immediately):

        #ingestion_props = IngestionProperties(database=database_name, table=table_name, data_format=DataFormat.CSV)
        ingestion_props = IngestionProperties(database=database_name, table=table_name, data_format=DataFormat.JSON,\
                                             ingestion_mapping_reference='json_mapping_01', \
                                             flush_immediately=flush_immediately,\
                                             report_level=ReportLevel.FailuresAndSuccesses)

        #TODO: add get file size code 
        file_descriptor = FileDescriptor(data_file_path, 15360)  # in this example, the raw (uncompressed) size of the data is 15KB (15360 bytes)
        ADXHelper.QUEUEDINGESTCLIENT.ingest_from_file(file_descriptor, ingestion_properties=ingestion_props)
        print("Finish Ingest From File")
        #QUEUEDINGESTCLIENT.ingest_from_file("{filename}.csv", ingestion_properties=ingestion_props)


    def run_kql_query(self,database_name,table_name):
        
        db = database_name
        query = "{} | count".format(table_name)

        print ("RUN KQL Query {}".format(query))
        response = ADXHelper.SERVICE_CLIENT.execute(db, query)
        for row in response.primary_results[0]:
            print (row[0])
            print (row)
            #print(row[0], " ", row["EventType"])


if __name__ == "__main__": # pragma: no cover
    init_config()
    initialize_kusto_client()

    # Get related arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('act', help='action will be performed', type=str, \
                        choices=["createDatabase", "createTableofDatabase", \
                        "deleteDatabase", "dropTables", "updateDatabaseIngestPolicy", \
                        "updateretentiondate", "runcsl"])
    parser.add_argument('-s', '--schemaFp', \
        help='Schema file. format: {field_name},{type},{value_source_str}', \
        type=str)
    parser.add_argument('-c', '--deviceCount', help='Device count. format: int',
                        type=int)
    args = parser.parse_args()

    # Retrieve parameters
    act = args.act
    schemaFp = args.schemaFp
    databaseCount = args.deviceCount

    # validate args. Error if schema file is not assigned
    if act in ("createTableofDatabase") \
        and (not schemaFp or not os.path.exists(schemaFp)):
        print("Please assign schema file path: -s /tmp/schema.csv")
        sys.exit(1)

    # run functions
    s = []
    if act == "createDatabase":
        create_database(databaseCount)
    elif act == "createTableofDatabase":
        create_table_of_database(databaseCount, schemaFp)
    elif act == "updateDatabaseIngestPolicy":
        update_ingestion_policy(databaseCount)
    elif act == "deleteDatabase":
        delete_database(databaseCount)
    elif act == "updateretentiondate":
        update_retention_date(databaseCount)
    elif act =="runcsl":
        run_adx_csl_command(databaseCount, schemaFp)
