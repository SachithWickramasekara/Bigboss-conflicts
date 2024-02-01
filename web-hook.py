# from .models import User
import datetime
import boto3
import os
import base64
from pymongo import MongoClient 
# from .utils import get_supplier_list
import botocore
import datetime
import time
import json
import trp.trp2 as t2
import pandas as pd
from text_parser import (
    table_to_json_new,
    tabledict_to_json,
    extract_text,
    map_word_id,
    extract_table_info,
    get_key_map,
    get_value_map,
    get_kv_map,
    add_to_json,
    table_to_json,
    stubdict_to_json,
    stub_table_to_df
)
from dotenv import load_dotenv
load_dotenv(".env")

client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client[f"{os.getenv('db_name')}"]
mycollection = mydatabase['users']  
uploads=mydatabase["uploads"]
tax_type=mydatabase["tax_type"]
line_item_data=mydatabase["line_item_data"]


bucket_name=os.getenv("bucket_name")
print(bucket_name)
aws_access_key=os.getenv("Access_key_ID")
aws_secret_key=os.getenv("Secret_access_key")
region=os.getenv("region")
s3 = boto3.client('s3',aws_access_key_id=aws_access_key,aws_secret_access_key=aws_secret_key)
textract = boto3.client('textract',region_name='us-east-1',aws_access_key_id="AKIA6LJ7T33HV53Q5EUU",aws_secret_access_key="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")

def list_files_in_folder(folder_name):
    # Add a "/" at the end of the folder name to ensure only files within the folder are listed
    if not folder_name.endswith('/'):
        folder_name += '/'
    
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)

    files = []
    for obj in response.get('Contents', []):
        # Extracting the file name from the full path
        file_name = obj['Key']
        files.append(file_name)

    return {folder_name:files}

def text_to_json_single(file_name):
        FeatureTypes=["FORMS", "TABLES"]
        invoice = s3.get_object(Bucket=bucket_name, Key=file_name)
        file = invoice['Body'].read()
        if file is not None:
                try:
                    response = textract.analyze_document(
                        Document={"Bytes": file},FeatureTypes=FeatureTypes
                        )
                    raw_text = extract_text(response, extract_by="LINE")
                    word_map = map_word_id(response)
                    table = extract_table_info(response, word_map)
                    key_map = get_key_map(response, word_map)
                    value_map = get_value_map(response, word_map)
                    final_map = get_kv_map(key_map, value_map)  
                    response_query = textract.analyze_document(
                    Document={'Bytes': file},
                        FeatureTypes=["QUERIES"],
                        QueriesConfig={
                            "Queries": [{
                                "Text": "What is the company name in the invoice?",
                                "Alias": "COMPANY_NAME"
                            },
                            {
                                "Text": "What is the company address in the invoice?",
                                "Alias": "COMPANY_ADDRESS"
                            },
                            {
                                "Text": "What is the receiver name in the invoice?",
                                "Alias": "RECEIVER_NAME"
                            },
                            {
                                "Text": "What is the receiver address in the invoice?",
                                "Alias": "RECEIVER_ADDRESS"
                            },
                            {
                                "Text": "What is the invoice date?",
                                "Alias": "INVOICE_DATE"
                            },
                            {
                                "Text": "What is the invoice number?",
                                "Alias": "INVOICE_NO"
                            },
                            {
                                "Text": "What is the due date in the invoice?",
                                "Alias": "DUE_DATE"
                            },
                            {
                                "Text": "What is the tax or GST amount in the invoice?",
                                "Alias": "TAX_AMOUNT"
                            },
                            {
                                "Text": "What is the total amount in the invoice?",
                                "Alias": "TOTAL"
                            }]
                        })
                    d = t2.TDocumentSchema().load(response_query)
                    page = d.pages[0]
                    query_answers = d.get_query_answers(page=page)
                    query_json_obj = add_to_json(query_answers)
                    df = table_to_json_new(table)
                    if df is not None:
                        table_json = tabledict_to_json(df)
                        jsonMerged = {**json.loads(query_json_obj), **json.loads(table_json)}
                    else:
                        jsonMerged = {**json.loads(query_json_obj)} 
                    return jsonMerged

                except Exception as e_raise:
                    print(e_raise)
                    return False

def stub_to_json_single(file_name):
        FeatureTypes=["FORMS", "TABLES"]
        invoice = s3.get_object(Bucket=bucket_name, Key=file_name)
        file = invoice['Body'].read()
        if file is not None:
                try:
                    response = textract.analyze_document(
                        Document={"Bytes": file},FeatureTypes=FeatureTypes
                        )
                    raw_text = extract_text(response, extract_by="LINE")
                    word_map = map_word_id(response)
                    table = extract_table_info(response, word_map)
                    key_map = get_key_map(response, word_map)
                    value_map = get_value_map(response, word_map)
                    final_map = get_kv_map(key_map, value_map)  
                    response_query = textract.analyze_document(
                    Document={'Bytes': file},
                        FeatureTypes=["QUERIES"],
                        QueriesConfig={
                            "Queries": [{
                                "Text": "What is the company name in the invoice?",
                                "Alias": "COMPANY_NAME"
                            },
                            {
                                "Text": "What is the company address in the invoice?",
                                "Alias": "COMPANY_ADDRESS"
                            },
                            {
                                "Text": "What is the receiver name in the invoice?",
                                "Alias": "RECEIVER_NAME"
                            },
                            {
                                "Text": "What is the receiver address in the invoice?",
                                "Alias": "RECEIVER_ADDRESS"
                            },
                            {
                                "Text": "What is the invoice date?",
                                "Alias": "INVOICE_DATE"
                            },
                            {
                                "Text": "What is the reference number or invoice number in the receipt?",
                                "Alias": "INVOICE_NO"
                            },
                            {
                                "Text": "What is the due date in the invoice?",
                                "Alias": "DUE_DATE"
                            },
                            {
                                "Text": "What is the tax or GST amount in the invoice?",
                                "Alias": "TAX_AMOUNT"
                            },
                            {
                                "Text": "What is the total amount in the invoice?",
                                "Alias": "TOTAL"
                            }]
                        })
                    d = t2.TDocumentSchema().load(response_query)
                    page = d.pages[0]
                    query_answers = d.get_query_answers(page=page)
                    query_json_obj = add_to_json(query_answers)
                    df = stub_table_to_df(table) 
                    if df is not None:
                        table_json = tabledict_to_json(df)
                        jsonMerged = {**json.loads(query_json_obj), **json.loads(table_json)}
                    else:
                        jsonMerged = {**json.loads(query_json_obj)}
                    return jsonMerged

                except Exception as e_raise:
                    print(e_raise)
                    return False                

def text_to_json_multiple(data):
    dict_of_df = {}
    count = 0
    # folder_name=data

    # try:
    for folder in data:
        print(folder,'this is from text to json function')
        if(len(data[folder])!=1):
            data[folder].sort()
            print(data[folder])
            for file in data[folder]:
                print(file,"thhis is file name that gets object")
                invoice = s3.get_object(Bucket=bucket_name, Key=file)
                file = invoice['Body'].read()
                if count == 0:
                    FeatureTypes=["FORMS", "TABLES"]
                    try:
                        response = textract.analyze_document(
                            Document={"Bytes": file},FeatureTypes=FeatureTypes
                            )
                        raw_text = extract_text(response, extract_by="LINE")
                        word_map = map_word_id(response)
                        table = extract_table_info(response, word_map)
                        key_map = get_key_map(response, word_map)
                        value_map = get_value_map(response, word_map)
                        final_map = get_kv_map(key_map, value_map)  
                        response_query = textract.analyze_document(
                        Document={'Bytes': file},
                            FeatureTypes=["QUERIES"],
                            QueriesConfig={
                                "Queries": [{
                                    "Text": "What is the company name in the invoice?",
                                    "Alias": "COMPANY_NAME"
                                },
                                {
                                    "Text": "What is the company address in the invoice?",
                                    "Alias": "COMPANY_ADDRESS"
                                },
                                {
                                    "Text": "What is the receiver name in the invoice?",
                                    "Alias": "RECEIVER_NAME"
                                },
                                {
                                    "Text": "What is the receiver address in the invoice?",
                                    "Alias": "RECEIVER_ADDRESS"
                                },
                                {
                                    "Text": "What is the invoice date?",
                                    "Alias": "INVOICE_DATE"
                                },
                                {
                                    "Text": "What is the invoice number?",
                                    "Alias": "INVOICE_NO"
                                },
                                {
                                    "Text": "What is the due date in the invoice?",
                                    "Alias": "DUE_DATE"
                                },
                                {
                                    "Text": "What is the tax or GST amount in the invoice?",
                                    "Alias": "TAX_AMOUNT"
                                },
                                {
                                    "Text": "What is the total amount in the invoice?",
                                    "Alias": "TOTAL"
                                }]
                            })
                        d = t2.TDocumentSchema().load(response_query)
                        page = d.pages[0]
                        query_answers = d.get_query_answers(page=page)
                        query_json_obj = add_to_json(query_answers)
                        dict_of_df[count] = table_to_json_new(table)
                        #table_val.append(table_to_json(table))
                        #jsonMerged = {**json.loads(query_json_obj), **json.loads(item_json_obj)}
                        json_str = json.dumps(query_json_obj)

                    except Exception as e_raise:
                        print(e_raise)
                        return False
                else:
                    FeatureTypes=["FORMS", "TABLES"]

                    try:
                        response = textract.analyze_document(
                            Document={"Bytes": file},FeatureTypes=FeatureTypes
                            )
                        word_map = map_word_id(response)
                        table = extract_table_info(response, word_map)
                        key_map = get_key_map(response, word_map)
                        value_map = get_value_map(response, word_map) 
                        dict_of_df[count] = table_to_json_new(table)

                    except Exception as e_raise:
                        print(e_raise)
                        return False
                count = count + 1
            if dict_of_df:
                        table_json = tabledict_to_json(dict_of_df)
                        jsonMerged = {**json.loads(query_json_obj), **json.loads(table_json)}
            else:
                        jsonMerged = {**json.loads(query_json_obj)} 
            print(jsonMerged)
          
        else:
            
            jsonMerged = text_to_json_single(data[folder][0])
            print(jsonMerged)
    return json.dumps(jsonMerged)

def stub_to_json_multiple(data):
    dict_of_df = {}
    count = 0
    # folder_name=data

    # try:
    for folder in data:
        print(folder,'this is from stub to json function')
        if(len(data[folder])!=1):
            for file in data[folder]:
                print(file,"this is file name that gets object")
                invoice = s3.get_object(Bucket=bucket_name, Key=file)
                file = invoice['Body'].read()
                
                if count == 1:
                    FeatureTypes=["FORMS", "TABLES"]
                    # Amazon S3 client
                    # Amazon Textract client
                    # textract = boto3.client('textract',region_name='us-east-1',aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)

                    # if file is not None:
                    #         with open(file, "rb") as document_file:
                    #             document_bytes = document_file.read()

                    try:
                        response = textract.analyze_document(
                            Document={"Bytes": file},FeatureTypes=FeatureTypes
                            )
                        raw_text = extract_text(response, extract_by="LINE")
                        word_map = map_word_id(response)
                        table = extract_table_info(response, word_map)
                        key_map = get_key_map(response, word_map)
                        value_map = get_value_map(response, word_map)
                        final_map = get_kv_map(key_map, value_map)  
                        response_query = textract.analyze_document(
                        Document={'Bytes': file},
                            FeatureTypes=["QUERIES"],
                            QueriesConfig={
                                "Queries": [{
                                    "Text": "What is the company name in the invoice?",
                                    "Alias": "COMPANY_NAME"
                                },
                                {
                                    "Text": "What is the company address in the invoice?",
                                    "Alias": "COMPANY_ADDRESS"
                                },
                                {
                                    "Text": "What is the receiver name in the invoice?",
                                    "Alias": "RECEIVER_NAME"
                                },
                                {
                                    "Text": "What is the receiver address in the invoice?",
                                    "Alias": "RECEIVER_ADDRESS"
                                },
                                {
                                    "Text": "What is the invoice date?",
                                    "Alias": "INVOICE_DATE"
                                },
                                {
                                    "Text": "What is the reference number or invoice number in the receipt?",
                                    "Alias": "INVOICE_NO"
                                },
                                {
                                    "Text": "What is the due date in the invoice?",
                                    "Alias": "DUE_DATE"
                                },
                                {
                                    "Text": "What is the tax or GST amount in the invoice?",
                                    "Alias": "TAX_AMOUNT"
                                },
                                {
                                    "Text": "What is the total amount in the invoice?",
                                    "Alias": "TOTAL"
                                }]
                            })
                        d = t2.TDocumentSchema().load(response_query)
                        page = d.pages[0]
                        query_answers = d.get_query_answers(page=page)
                        query_json_obj = add_to_json(query_answers)
                        dict_of_df[count] = stub_table_to_df(table)
                        #table_val.append(table_to_json(table))
                        #jsonMerged = {**json.loads(query_json_obj), **json.loads(item_json_obj)}
                        json_str = json.dumps(query_json_obj)

                    except Exception as e_raise:
                        print(e_raise)
                        return False
                else:
                    FeatureTypes=["FORMS", "TABLES"]
                    # Amazon S3 client
                   
                    # Amazon Textract client
                    # textract = boto3.client('textract',region_name='us-east-1',aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)

                    # if file is not None:
                    #         with open(file, "rb") as document_file:
                    #             document_bytes = document_file.read()

                    try:
                        response = textract.analyze_document(
                            Document={"Bytes": file},FeatureTypes=FeatureTypes
                            )
                        word_map = map_word_id(response)
                        table = extract_table_info(response, word_map)
                        key_map = get_key_map(response, word_map)
                        value_map = get_value_map(response, word_map) 
                        dict_of_df[count] = stub_table_to_df(table)

                    except Exception as e_raise:
                        print(e_raise)
                        return False
                count = count + 1
    
            if dict_of_df:
                        table_json = tabledict_to_json(dict_of_df)
                        jsonMerged = {**json.loads(query_json_obj), **json.loads(table_json)}
            else:
                        jsonMerged = {**json.loads(query_json_obj)} 
            
            print(jsonMerged)

    # except Exception as e_raise:
    #     print(e_raise)
    #     return False              
        else:
            
            jsonMerged = stub_to_json_single(data[folder][0])
            print(jsonMerged)
    return json.dumps(jsonMerged)

all_queries = [{
                                    "Text": "What is the company name in the invoice?",
                                    "Alias": "COMPANY_NAME"
                                },
                                {
                                    "Text": "What is the company address in the invoice?",
                                    "Alias": "COMPANY_ADDRESS"
                                },
                                {
                                    "Text": "What is the receiver name in the invoice?",
                                    "Alias": "RECEIVER_NAME"
                                },
                                {
                                    "Text": "What is the receiver address in the invoice?",
                                    "Alias": "RECEIVER_ADDRESS"
                                },
                                {
                                    "Text": "What is the invoice date?",
                                    "Alias": "INVOICE_DATE"
                                },
                                {
                                    "Text": "What is the invoice number?",
                                    "Alias": "INVOICE_NO"
                                },
                                {
                                    "Text": "What is the due date in the invoice?",
                                    "Alias": "DUE_DATE"
                                },
                                {
                                    "Text": "What is total GST?",
                                    "Alias": "TAX_AMOUNT"
                                },
                                {
                                    "Text": "What is the total amount in the invoice?",
                                    "Alias": "TOTAL"
            }]

answers = {}

def convert_queries_todict(queries):
    queries_dict = {}
    key=0
    for query in queries:
        query_new = {
             "Alias":query[1],
             "Answer":query[2]
        }
        queries_dict[key]= query_new
        key+=1
    return queries_dict

def text_to_json_multiple_new(data):
    # folder_name=data

    # try:
    for folder in data:
        print(folder,'this is from text to json function')
        if(len(data[folder])!=1):
            data[folder].sort()
            for file in data[folder]:
                queries = [query for query in all_queries if query["Alias"] not in answers]
                print("Current List of Queries:",queries)
                print(file,"thhis is file name that gets object")
                if(len(queries)!=0):
                    invoice = s3.get_object(Bucket=bucket_name, Key=file)
                    file = invoice['Body'].read()
                    try:
                            response_query = textract.analyze_document(
                            Document={'Bytes': file},
                                FeatureTypes=["QUERIES"],
                                QueriesConfig={"Queries": queries})
                            d = t2.TDocumentSchema().load(response_query)
                            page = d.pages[0]
                            q = d.get_query_answers(page=page)
                            query_answers = convert_queries_todict(q)
                            # Update the dictionary of answers with the new answers
                            for answer in query_answers.values():
                                if answer["Alias"] not in answers and answer["Answer"] != '':
                                    answers[answer["Alias"]] = answer["Answer"]
                            print(answers)

                    except Exception as e_raise:
                            print(e_raise)
                            return False
            
    return json.dumps(answers)
                

def get_from_temp():
    data=s3.list_objects(Bucket=bucket_name,Prefix="TEMP")
    try:
        result_dict = {}
        for i in data["Contents"]:
            # print(i)
            base_name = i["Key"].split('/')[1]
            if base_name in result_dict:
                result_dict[base_name].append(i["Key"] )
            else:
                result_dict[base_name] = [i["Key"]]
        print(result_dict)
        return result_dict
    except KeyError:
        return False

def get_folders_from_processing_to_temp():
    data=s3.list_objects(Bucket=bucket_name,Prefix="bills-processing")
    try:
        result_dict = {}
        for i in data["Contents"]:
            base_name = i["Key"].split('/')[1]
            if base_name in result_dict:
                result_dict[base_name].append(i["Key"] )
            else:
                result_dict[base_name] = [i["Key"]]
        print(result_dict)
        for folder in result_dict:
                print(folder)
                per_file=result_dict[folder]
                for file in per_file:
                    new_object_key = file.replace("bills-processing", "TEMP", 1)
                    s3.copy_object(
                    Bucket=bucket_name,
                    CopySource={'Bucket': bucket_name, 'Key': file},
                    Key=new_object_key
                    )
                    s3.delete_object(Bucket=bucket_name, Key=file)
                    print(f"moved {folder} to temp folder" )
        return True
    except KeyError:
        return False

def move_to_processed(source_folder):
    destination_folder = 'PROCESSED/'
    response = s3.list_objects(Bucket=bucket_name)
    for obj in response['Contents']:
        source_key = obj['Key']
        if source_folder in source_key:
            s3.copy_object(
                Bucket=bucket_name,
                CopySource={'Bucket': bucket_name, 'Key': source_key},
                Key=destination_folder+source_key.replace("TEMP/","")
            )
            s3.delete_object(Bucket=bucket_name, Key=source_key)


def run_process(data):
    filtered_data = {key: value for key, value in data.items() if key != ''}

    try:
        folder=next(iter(filtered_data))
        print(folder,"this data from run process")
        # doc_type = uploads.find_one({"document_name":folder},{"document_type":1,"_id":0})
        doc_type=uploads.find_one({"document_name":folder})
        # for d in doc_type:
        #     # print(d['document_type'])
        #     d_type=d["document_type"]
        try:
            if doc_type["document_type"] == 'invoice':
                text_data=text_to_json_multiple_new(data=filtered_data)
            else:
                text_data=stub_to_json_multiple(data = filtered_data)
            if text_data:
                uploads.update_one({"document_name":folder},{'$set':{"line_item":text_data,"status":'In-Progress'}})
                print("updated in mongo")
                move_to_processed(folder)
                print(f"process finished for {folder}")
            else:
                print(text_data,"process failed")
        except Exception as e:
            print(e)

                
                # print(text_data)
                
    except:
        "pass"
print('starting ')


while True:
    time.sleep(10)
    get_folders_from_processing_to_temp() # make this as schudluer
    datas=get_from_temp()
    print(datas,"this is data")
    if datas:
        try:
            run_process(data=datas)
        except:
            print("unable to run process.....")