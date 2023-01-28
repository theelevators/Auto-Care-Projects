import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from pyodbc import Cursor
import pyodbc
import pandas as pd
from pandas import DataFrame
import os
import json
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

# Set Up ENV Variables
db = os.environ["DB"]
server = os.environ["SERVER"]
tmp = open(os.environ["TABLES"])
imprt = open(os.environ["IMPORT"])

tmp_table = json.loads(tmp.read())
imp_table = json.loads(imprt.read())

conn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                      f"Server={server};"
                      f"Database={db};"
                      "Trusted_Connection=yes;")

def create_insert_query(table: dict) -> str:
    cols = list(table.values())[0]
    table_name = list(table.keys())[0]
    cols_num = len(cols)
    values = ['?']*cols_num
    insert_cols = ''.join(str(val) + ', ' if idx < len(cols) -
                          1 else str(val) for idx, val in enumerate(cols))
    insert_values = ''.join(str(val) + ', ' if idx < len(values) -
                            1 else str(val) for idx, val in enumerate(values))
    query = f"INSERT INTO {table_name} ({insert_cols}) VALUES ({insert_values})"

    return query

def import_to_database(cursor: Cursor, import_rows: list, query: str) -> str:
    num_rows = len(import_rows)
    if num_rows == 1:
        try:
            cursor.execute(query, import_rows)
            return "OK"
        except Exception as err:
            return err
    else:
        try:
            cursor.executemany(query, import_rows)
            return "OK"
        except Exception as err:
            return err

def start_import(cursor: Cursor, table: dict, dataFrame: DataFrame) -> str:

    for key, value in table.items():
        rows = prepare_insert(dataFrame, key)
        import_row = rows.to_numpy().tolist()
        query = create_insert_query(value)
        
        response = import_to_database(
            cursor=cursor, import_rows=import_row, query=query)

        if response != "OK":
            message = f"An error has occurred while importing in {key}s. Error: {response}"
            return message
        
    return f"Import succesfully completed!"

def get_headers_info(element: Element, namespace: str) -> list:
    elements = []
    for element in element:
        key = element.tag
        key = key.replace(namespace, '')
        elements.append({key: element.text})
    return(elements)

def has_sub(element:Element)->bool:
    sub_elements = [sub for sub in element]
    if len(sub_elements) > 0:
        return True
    else:
        return False

def get_sub_elements(flag: bool, element: Element, details: dict, namespace: str) -> None:
    if flag == True:
        for sub in element:
            primary_tag = element.tag
            primary_tag = primary_tag.replace(namespace, '')
            if primary_tag == 'DigitalFileInformation':

                sub_digital = {s.tag.replace(namespace, ''): s.text.replace(
                    namespace, '') for s in element}

                record = {
                    "PartNumber": details['PartNumber'],
                    "BrandAAIAID": details['BrandAAIAID'],
                    "PartTerminologyID": details['PartTerminologyID'],
                    "Segment": primary_tag
                }

                record.update(sub_digital)
                details['records'].append(record)
            else:
                get_sub_elements(has_sub(sub), sub, details, namespace)
    else:
        key = element.tag
        key = key.replace(namespace, '')

        if key in details:
            if len(element.attrib) > 0:
                text = element.text
                record = {
                    "PartNumber": details['PartNumber'],
                    "BrandAAIAID": details['BrandAAIAID'],
                    "PartTerminologyID": details['PartTerminologyID'],
                    "Segment": key,
                    "Value": text if text != '' else None
                }
                record.update(element.attrib)
                details['records'].append(record)

                return
            else:
                details[key] = element.text
                return

def create_product_list(root: Element, namespace: str) -> list:
    item_elements = root.findall(f"./{namespace}Items/{namespace}Item")
    product_list = []
    for element in item_elements:
        details = {
            "PartNumber": "",
            "BrandAAIAID": "",
            "PartTerminologyID": "",
            "Description": "",
            "ExtendedProductInformation": "",
            "ProductAttribute": "",
            "DigitalFileInformation": "",
            "records": []
        }

        get_sub_elements(has_sub(element=element), element,
                         details, namespace=namespace)

        product_list.extend(details['records'])

    return product_list

def prepare_insert(dataFrame: DataFrame, segment: str) -> DataFrame:
    results = dataFrame.query('Segment == "%s"' % segment)
    results = results.dropna(axis=1, how='all')
    return results

def xml_parse(obj: dict) -> str:
    
    if obj['validated'] == False:
        return "File must pass validation before importing. Please validate file."
    
    namespace = '{http://www.autocare.org}'
    file_name = obj['file']
    tree = ET.parse(file_name)
    root = tree.getroot()
    data = create_product_list(root=root, namespace=namespace)
    dataFrame = pd.json_normalize(data)
    cursor = conn.cursor()


    return start_import(cursor,tmp_table,dataFrame )
