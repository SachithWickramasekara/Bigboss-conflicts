import json
import numpy as np
import uuid
from datetime import datetime
import re
import os
import copy
import pandas as pd
from difflib import get_close_matches
from pymongo import MongoClient 
from dotenv import load_dotenv
load_dotenv(".env")

client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client["Bigboss"]
acc_type = mydatabase['account_type'] 

def closeMatches(patterns, word):
     matches= get_close_matches(word, patterns)
     if matches:
      return matches[0]
     else:
      return None
     
def find_account_code(company):
    company = company.title()
    print(company)
    try:
        data = acc_type.find({"Name":company},{"Account Allocation":1,"_id":0})
        for d in data:
            c_code = d['Account Allocation']
        return c_code
    except:
        c_code = ""
        return c_code
    
def find_company_match(company):
    try:
        company_list = acc_type.distinct("Name")
        company_list = [x.lower() for x in company_list]
        c_name = closeMatches(company_list,company)
        return c_name
    except:
        return False

def extract_text(response, extract_by="WORD"):
    line_text = []
    for block in response["Blocks"]:
        if block["BlockType"] == extract_by:
            line_text.append(block["Text"])
    return line_text

def extract_number(val):
    match = re.search(r'\d+(\.\d+)?', val)
    return match.group(0) if match else val

def extract_numbers(val):
    return re.findall(r'\d+(?:\.\d+|'')', val.replace(',', ''))

def is_number(val):
    try:
        float(val)
        return True
    except ValueError:
        return False

def map_word_id(response):
    word_map = {}
    for block in response["Blocks"]:
        if block["BlockType"] == "WORD":
            word_map[block["Id"]] = block["Text"]
        if block["BlockType"] == "SELECTION_ELEMENT":
            word_map[block["Id"]] = block["SelectionStatus"]
    return word_map


def extract_table_info(response, word_map):
    row = []
    table = {}
    ri = 0
    flag = False

    for block in response["Blocks"]:
        if block["BlockType"] == "TABLE":
            key = f"table_{uuid.uuid4().hex}"
            table_n = +1
            temp_table = []

        if block["BlockType"] == "CELL":
            if block["RowIndex"] != ri:
                flag = True
                row = []
                ri = block["RowIndex"]

            if "Relationships" in block:
                for relation in block["Relationships"]:
                    if relation["Type"] == "CHILD":
                        row.append(" ".join([word_map[i] for i in relation["Ids"]]))
            else:
                row.append(" ")

            if flag:
                temp_table.append(row)
                table[key] = temp_table
                flag = False
    return table


def get_key_map(response, word_map):
    key_map = {}
    for block in response["Blocks"]:
        if block["BlockType"] == "KEY_VALUE_SET" and "KEY" in block["EntityTypes"]:
            for relation in block["Relationships"]:
                if relation["Type"] == "VALUE":
                    value_id = relation["Ids"]
                if relation["Type"] == "CHILD":
                    v = " ".join([word_map[i] for i in relation["Ids"]])
                    key_map[v] = value_id
    return key_map


def get_value_map(response, word_map):
    value_map = {}
    for block in response["Blocks"]:
        if block["BlockType"] == "KEY_VALUE_SET" and "VALUE" in block["EntityTypes"]:
            if "Relationships" in block:
                for relation in block["Relationships"]:
                    if relation["Type"] == "CHILD":
                        v = " ".join([word_map[i] for i in relation["Ids"]])
                        value_map[block["Id"]] = v
            else:
                value_map[block["Id"]] = "VALUE_NOT_FOUND"

    return value_map


def get_kv_map(key_map, value_map):
    final_map = {}
    for i, j in key_map.items():
        final_map[i] = "".join(["".join(value_map[k]) for k in j])
    return final_map


# def print_values_form(final_map):  
#   final_df = pd.DataFrame(columns = ['Keys','Values'])
#   field_df = pd.DataFrame(columns = ['Keys','Values'])
#   for key, value in final_map.items():
#     df = pd.DataFrame(columns = ['Keys','Values'])
#     df = df.append(pd.DataFrame({"Keys":[key], "Values": [value]}))
#     if(key=="Acct #" or key == "Mamber Name" or key =="Check Number" or key =="Check Amount" or key == "CO22" or key == "CO97" or key == "MA67" or key == "N19" or key == "Member number"):
#        field_df.append(pd.DataFrame({"Keys":[key], "Values": [value]}))
#     final_df = final_df.append(df)
  
#   return field_df

def print_json_table(table):
  dict_of_df = {}
  keyss = table.keys()

  for t, key in enumerate(keyss):
    key_name = 'table_'+str(t)
    df=pd.DataFrame(table[key])
    dict_of_df[key_name] = copy.deepcopy(df)

  df_key = dict_of_df.keys()
  
  for key in df_key:
    print(key)
    json_columns = dict_of_df[key].to_json()
    print(json_columns)

    
def print_values_table(table):
   dict_of_df = {}
   keyss = table.keys()
   for t, key in enumerate(keyss):
    key_name = 'table_'+str(t)
    df=pd.DataFrame(table[key])
    dict_of_df[key_name] = copy.deepcopy(df)
   
   df_key = dict_of_df.keys()
   for key in df_key:
    print ("\n-----------------------------------------------------------------------\n")
    print(dict_of_df[key])

# def print_json_table(table):
#   dict_of_df = {}
#   keyss = table.keys()

#   for t, key in enumerate(keyss):
#     key_name = 'table_'+str(t)
#     df=pd.DataFrame(table[key])
#     dict_of_df[key_name] = copy.deepcopy(df)

#   df_key = dict_of_df.keys()
#   return dict_of_df

#   for key in df_key:
#     print(key)
#     json_columns = dict_of_df[key].to_json()
#     print(json_columns)


# def print_values_table(table):
#   dict_of_df = {}
#   keyss = table.keys()

#   for t, key in enumerate(keyss):
#     key_name = 'table_'+str(t)
#     df=pd.DataFrame(table[key])
#     dict_of_df[key_name] = copy.deepcopy(df)

#   df_key = dict_of_df.keys()

#   for key in df_key:
#     print ("\n-----------------------------------------------------------------------\n")
#     print(dict_of_df[key])

def print_values_form(final_map):
  final_df = pd.DataFrame(columns = ['Keys','Values'])
  for key, value in final_map.items():
    df = pd.DataFrame(columns = ['Keys','Values'])
    df = df._append(pd.DataFrame({"Keys":[key], "Values": [value]}))
    final_df = final_df._append(df)

  return final_df

def countList(lst):
    return sum(type(el)== type([]) for el in lst)

def serialize_datetime(obj): 
    if isinstance(obj, datetime.datetime): 
        return obj.isoformat() 
    raise TypeError("Type not serializable") 

def add_to_json(query_answers):
    print(query_answers)
    tax_percent = 10
    for answer in query_answers:
                if answer[1] == "COMPANY_NAME":
                    company_name = answer[2]
                elif answer[1] == "COMPANY_ADDRESS":
                    company_address = answer[2]
                elif answer[1] == "RECEIVER_NAME":
                    receiver_name = answer[2]
                elif answer[1] == "RECEIVER_ADDRESS":
                    receiver_address = answer[2]
                elif answer[1] == "INVOICE_DATE":
                        
                        if re.findall(r'\d{1,2}-\d{1,2}-\d{4}', answer[2]):
                            due_date = datetime.strptime(answer[2],"%d-%m-%Y")
                            invoice_date = due_date.strftime("%Y-%m-%d")
                        elif re.findall(r'\d{1,2}/\d{1,2}/\d{4}', answer[2]):
                            due_date = datetime.strptime(answer[2],"%d/%m/%Y")
                            invoice_date = due_date.strftime("%Y/%m/%d")
                        elif re.findall(r'\d{1,2} \d{1,2} \d{4}', answer[2]):
                            due_date = datetime.strptime(answer[2],"%d %m %Y")
                            invoice_date = due_date.strftime("%Y %m %d")
                        elif re.findall(r'\d{4}-\d{1,2}-\d{1,2}', answer[2]):
                            due_date = datetime.strptime(answer[2],"%Y-%m-%d")
                            invoice_date = due_date.strftime("%Y-%m-%d")
                        elif re.findall(r'\d{4}/\d{1,2}/\d{1,2}', answer[2]):
                            due_date = datetime.strptime(answer[2],"%Y/%m/%d")
                            invoice_date = due_date.strftime("%Y/%m/%d")
                        elif re.findall(r"\d{1,2} [A-Z][a-z][a-z] \d{4}",answer[2]):
                            due_date = datetime.strptime(answer[2],"%d %b %Y")
                            invoice_date = due_date.strftime("%Y %m %d") 
                        elif re.findall(r"\d{1,2}-[A-Z][a-z][a-z]-\d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d-%b-%Y")
                            invoice_date = dt.strftime("%Y-%m-%d")
                        elif re.findall(r"\d{1,2} [A-Z][a-z][a-z] \d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d %b %Y")
                            invoice_date = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2} [A-Z][A-Z][A-Z] \d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d %b %Y")
                            invoice_date = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2}-[A-Z][A-Z][A-Z]-\d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d-%b-%Y")
                            invoice_date = dt.strftime("%Y-%m-%d")
                        elif re.findall(r"\d{1,2}(?:th|st|nd|rd) [A-Z][A-Z][A-Z] \d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d %b %Y")
                            invoice_date = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2}(?:th|st|nd|rd) [A-Z][A-Z][A-Z] \d{2}",answer[2]):
                            match = re.search(r"(\d{2})(?:th|st|nd|rd) ([A-Z][A-Z][A-Z]) (\d{2})", answer[2])
                            if match:
                                day = match.group(1)
                                year = match.group(3)
                                month = match.group(2)
                                date = day + " " + month + " " + "20"+year
                            dt = datetime.strptime(date,"%d %b %Y")
                            invoice_date = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2}(?:th|st|nd|rd)-[A-Z][A-Z][A-Z]-\d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d-%b-%Y")
                            invoice_date = dt.strftime("%Y-%m-%d")
                        elif re.findall(r"\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d %B %Y")
                            invoice_date = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2}-(?:January|February|March|April|May|June|July|August|September|October|November|December)-\d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d-%B-%Y")
                            invoice_date = dt.strftime("%Y-%m-%d")
                        elif re.findall(r"\d{1,2}(?:th|st|nd|rd) (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{2}",answer[2]):
                            match = re.search(r"(\d{2})(?:th|st|nd|rd) (?:January|February|March|April|May|June|July|August|September|October|November|December) (\d{2})", answer[2])
                            if match:
                                day = match.group(1)
                                year = match.group(3)
                                month = match.group(2)
                                date = day + " " + month + " " + "20"+year
                            dt = datetime.strptime(date,"%d %B %Y")
                            invoice_date = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2}-[A-Z][a-z][a-z]-\d{2}",answer[2]):
                            match = re.search(r"(\d{2})-([A-Z][a-z][a-z])-(\d{2})", answer[2])
                            if match:
                                day = match.group(1)
                                year = match.group(3)
                                month = match.group(2)
                                date = day + " " + month + " " + "20"+year
                            dt = datetime.strptime(date,"%d %b %Y")
                            invoice_date = dt.strftime("%Y %m %d") 
                        else:
                            invoice_date = answer[2]
                elif answer[1] == "INVOICE_NO":
                    invoice_no = answer[2]
                elif answer[1] == "DUE_DATE":
                    #if countList(answer[2]) != 0:
                        if re.findall(r'\d{1,2}-\d{1,2}-\d{4}', answer[2]):
                            due_date = datetime.strptime(answer[2],"%d-%m-%Y")
                            dt_str = due_date.strftime("%Y-%m-%d")
                        elif re.findall(r'\d{1,2}/\d{1,2}/\d{4}', answer[2]):
                            due_date = datetime.strptime(answer[2],"%d/%m/%Y")
                            dt_str = due_date.strftime("%Y/%m/%d")
                        elif re.findall(r'\d{1,2} \d{1,2} \d{4}', answer[2]):
                            due_date = datetime.strptime(answer[2],"%d %m %Y")
                            dt_str = due_date.strftime("%Y %m %d")
                        elif re.findall(r'\d{4}-\d{1,2}-\d{1,2}', answer[2]):
                            due_date = datetime.strptime(answer[2],"%Y-%m-%d")
                            dt_str = due_date.strftime("%Y-%m-%d")
                        elif re.findall(r'\d{4}/\d{1,2}/\d{1,2}', answer[2]):
                            due_date = datetime.strptime(answer[2],"%Y/%m/%d")
                            dt_str = due_date.strftime("%Y/%m/%d")
                        elif re.findall(r"\d{1,2} [A-Z][a-z][a-z] \d{4}",answer[2]):
                            due_date = datetime.strptime(answer[2],"%d %b %Y")
                            dt_str = due_date.strftime("%Y %m %d") 
                        elif re.findall(r"\d{1,2}-[A-Z][a-z][a-z]-\d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d-%b-%Y")
                            dt_str = dt.strftime("%Y-%m-%d")
                        elif re.findall(r"\d{1,2} [A-Z][a-z][a-z] \d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d %b %Y")
                            dt_str = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2} [A-Z][A-Z][A-Z] \d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d %b %Y")
                            dt_str = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2}-[A-Z][A-Z][A-Z]-\d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d-%b-%Y")
                            dt_str = dt.strftime("%Y-%m-%d")
                        elif re.findall(r"\d{1,2}(?:th|st|nd|rd) [A-Z][A-Z][A-Z] \d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d %b %Y")
                            dt_str = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2}(?:th|st|nd|rd) [A-Z][A-Z][A-Z] \d{2}",answer[2]):
                            match = re.search(r"(\d{2})(?:th|st|nd|rd) ([A-Z][A-Z][A-Z]) (\d{2})", answer[2])
                            if match:
                                day = match.group(1)
                                year = match.group(3)
                                month = match.group(2)
                                date = day + " " + month + " " + "20"+year
                            dt = datetime.strptime(date,"%d %b %Y")
                            dt_str = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2}(?:th|st|nd|rd)-[A-Z][A-Z][A-Z]-\d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d-%b-%Y")
                            dt_str = dt.strftime("%Y-%m-%d")
                        elif re.findall(r"\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d %B %Y")
                            dt_str = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2}-(?:January|February|March|April|May|June|July|August|September|October|November|December)-\d{4}",answer[2]):
                            dt = datetime.strptime(answer[2],"%d-%B-%Y")
                            dt_str = dt.strftime("%Y-%m-%d")
                        elif re.findall(r"\d{1,2}(?:th|st|nd|rd) (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{2}",answer[2]):
                            match = re.search(r"(\d{2})(?:th|st|nd|rd) (?:January|February|March|April|May|June|July|August|September|October|November|December) (\d{2})", answer[2])
                            if match:
                                day = match.group(1)
                                year = match.group(3)
                                month = match.group(2)
                                date = day + " " + month + " " + "20"+year
                            dt = datetime.strptime(date,"%d %B %Y")
                            dt_str = dt.strftime("%Y %m %d")
                        elif re.findall(r"\d{1,2}-[A-Z][a-z][a-z]-\d{2}",answer[2]):
                            match = re.search(r"(\d{2})-([A-Z][a-z][a-z])-(\d{2})", answer[2])
                            if match:
                                day = match.group(1)
                                year = match.group(3)
                                month = match.group(2)
                                date = day + " " + month + " " + "20"+year
                            dt = datetime.strptime(date,"%d %b %Y")
                            dt_str = dt.strftime("%Y %m %d") 
                        else:
                            dt_str = answer[2]
                        #due_date = answer[2]
                    #else:
                        #due_date = answer[2]
                
                elif answer[1] == "TOTAL":
                    try:
                        total = float(extract_numbers(answer[2])[0])
                    except:
                        total = ""
                    print(total)
                elif answer[1] == "TAX_AMOUNT":
                    try:
                        tax_amount = float(extract_numbers(answer[2])[0])
                    except:
                        tax_amount = ''
                    print(tax_amount)
    if((tax_amount!=0 and tax_amount !='') and total!=""):
        taxable_amount = (tax_amount*100)/tax_percent
        if taxable_amount == total:
            non_taxable_amount = 0.0
        else:
            non_taxable_amount = total - taxable_amount
    elif (tax_amount==0 or tax_amount =='') and total!="":
        non_taxable_amount = total
        taxable_amount = 0.0
    else: 
        non_taxable_amount = 0.0
        taxable_amount = 0.0
    obj = { "invoice_from": {"name": company_name, "address": company_address},
            "invoice_to": {"name": receiver_name, "address": receiver_address},
            "invoice_date": invoice_date,
            "invoice_no": invoice_no,
            "due_date": dt_str,
            "tax_rate": tax_percent,
            "Total Bill Amount": total,
            "Tax Amount": tax_amount,
            "line_items": {"0":{"Description": company_name,"Quantity": 1.0 ,"UnitAmount": taxable_amount, "TotalAmount": taxable_amount},
            "1":{"Description": company_name,"Quantity": 1.0 ,"UnitAmount": non_taxable_amount, "TotalAmount": non_taxable_amount}}
          }
    y = json.dumps(obj)
    print(y)
    return y

def table_to_json(table):
        dict_of_df = {}
        keyss = table.keys()
        for t, key in enumerate(keyss):
            key_name = 'table_'+str(t)
            df=pd.DataFrame(table[key])
            dict_of_df[key_name] = copy.deepcopy(df)
        df = dict_of_df[key_name]
        #print(df)
        df.columns = df.iloc[0]
        df = df[1:]
        col = list(df.columns)
        
        for i in range(len(col)):
            if "qty" in col[i].lower() or "quantity" in col[i].lower():
                col[i] = "Quantity"
            elif "description" in col[i].lower() or "desc" in col[i].lower() or "item" in col[i].lower() or "product" in col[i].lower() or "name" in col[i].lower():
                col[i] = "Description"
            elif "unit" in col[i].lower() or "rate" in col[i].lower() or "price" in col[i].lower():
                col[i] = "UnitAmount"
        df.columns = col
        df_new = df[["Quantity","Description","UnitAmount"]]
        #print(col)
        # for i in range(len(df_new)):
        #     row_list = []
        #     for j in range(len(col)):
        #         row_list.append(df_new.iloc[i,j])
        #     values[i] = dict(zip(col,row_list))
        #     # print(values)
        #     # if i == 0:
        #     #     x = {"line_items": values[i]}
        #     # else:
        #     #     x.update(values)
        # x = {"line_items": values}
        # json_obj = json.dumps(x)
        return df_new

def tabledict_to_json(dict_of_df):
        if isinstance(dict_of_df, pd.DataFrame):
            df_new = dict_of_df
        else:
            df_new = pd.concat(dict_of_df, axis=0)
        print(df_new)
        values = {}
        col = list(df_new.columns)
        for i in range(len(df_new)):
            row_list = []
            for j in range(len(col)):
                value = df_new.iloc[i,j]
                # if isinstance(value, np.int64):
                #     value = float(value)
                row_list.append(value)
            values[i] = dict(zip(col,row_list))
            # print(values)
            # if i == 0:
            #     x = {"line_items": values[i]}
            # else:
            #     x.update(values)
        x = {"line_items": values}
        json_obj = json.dumps(x)
        return json_obj

def stubdict_to_json(dict_of_df):
        if isinstance(dict_of_df, pd.DataFrame):
            df_new = dict_of_df
        else:
            df_new = pd.concat(dict_of_df, axis=0)
        print(df_new)
        values = {}
        col = list(df_new.columns)
        for i in range(len(df_new)):
            row_list = []
            for j in range(len(col)):
                value = df_new.iloc[i,j]
                # if isinstance(value, np.int64):
                #     value = float(value)
                row_list.append(value)
            values[i] = dict(zip(col,row_list))
            # print(values)
            # if i == 0:
            #     x = {"line_items": values[i]}
            # else:
            #     x.update(values)
        x = {"line_items": values}
        json_obj = json.dumps(x)
        return json_obj

def stub_table_to_df(table):
    dict_of_df = []
    tables_final = []
    table_count = 0
    df_final = pd.DataFrame()
    for key in table.keys():
        dict_of_df.append(pd.DataFrame(table[key]))
    
    for t in range(len(dict_of_df)-1):
        flag = 0
        flag_x = 0
        total = 0
        df=pd.DataFrame(dict_of_df[t])
        for value in df[df.columns[0]].str.lower():
            if re.search(r'\w*(each|qty|kg|gm|net|[0-9]g|descr)\w*', value):
                flag_x = 1
                break    
        if flag_x == 1:
            if ("descr" in df.iloc[0, 0].lower().strip() or "item" in df.iloc[0, 0].lower().strip()) and ("total" in df.iloc[0, 1].lower().strip() or "amount" in df.iloc[0, 1].lower().strip()):
                df.iloc[0,0] = "Description"
                df.iloc[0,1] = "Amount"
                df = df.iloc[:,[0,1]]
                df.columns = df.iloc[0]
                df = df.iloc[1:]
            elif ("descr" in df.iloc[0, 0].lower().strip() or "item" in df.iloc[0, 0].lower().strip()) and ("total" in df.iloc[0, 2].lower().strip() or "amount" in df.iloc[0, 2].lower().strip()):
                df.iloc[0,0] = "Description"
                df.iloc[0,1] = "Amount"
                df.iloc[:,1]=df.iloc[:,2]
                df = df.iloc[:,[0,1]]
                df.columns = df.iloc[0]
                df = df.iloc[1:]
            else:
                df.columns = ["Description", "Amount"]
            
            df = df[~df.apply(lambda row: (row[0].strip() == '' and row[1].strip() == ''), axis=1)]
            df = df.reset_index(drop=True)
            df = df.applymap(lambda x: " " if pd.isnull(x) or str(x).strip() == "" else x)
            while df.iloc[-1][df.columns[1]] == " ":
                df = df.iloc[:-1]
            for index_row, row in df.iterrows():
                    if df.iloc[index_row,1] == " ":
                        if index_row + 1 < len(df):
                            df.iloc[index_row+1, 0] = df.iloc[index_row, 0] + ' ' + df.iloc[index_row + 1, 0]       
            
            df = df.loc[df[df.columns[1]] != " "]
            df = df.reset_index(drop=True)
            df[df.columns[1]] = df[df.columns[1]].str.replace('$', '')
            df['Amount'] = df['Amount'].apply(lambda x: extract_number(str(x)) if not str(x).isdigit() else x)
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            df = df[~df[df.columns[1]].apply(lambda x: isinstance(x, str))]
            for index_row, row in df.iterrows():
                    if np.isnan(df.iloc[index_row,1]):
                        if index_row + 1 < len(df):
                            df.iloc[index_row+1, 0] = df.iloc[index_row, 0] + ' ' + df.iloc[index_row + 1, 0]
            df = df.dropna(subset=[df.columns[1]])
            df = df.reset_index(drop=True)
            for index_row, row in df.iterrows():
                if re.findall("total",df.iloc[index_row,0].lower()):
                    flag = 1
                    total = df.iloc[index_row,1]
            if flag == 0:
                if t + 1 < len(dict_of_df):
                    df_new = dict_of_df[t+1]
                    if "total" in df_new.iloc[0,0].lower() or "number of items" in df_new.iloc[0,0]:
                        if("total" in df_new.iloc[0,0].lower() and (df_new.iloc[0,1]=='' or df_new.iloc[0,1]==" ")):
                            df_new.iloc[0,1] = df_new.iloc[1,1]
                        df_new.columns = ["Description", "Amount"]
                        df = pd.concat([df,df_new],axis=0)
                        del dict_of_df[t+1]
                    else:
                        df.loc[len(df)] = ["Total Amount", df[df.columns[1]].sum()]
                else:
                    df.loc[len(df)] = ["Total Amount", df[df.columns[1]].sum()]
            else:
                df.loc[len(df)] = ["Total Amount", total]
            df.reset_index(drop=True)
            df['Quantity'] = 1.0
            df['UnitAmount'] = df['Amount']
            df = df.rename(columns={'Amount': 'TotalAmount'})
            df = df.reindex(columns=['Description','Quantity', 'UnitAmount', 'TotalAmount'])
            #tables_final[table_count] = df
            tables_final.append(df)
            table_count += 1
            df_final = pd.concat([df_final,df],axis=0)
            
    return df_final

def table_to_json_new(table):
        dict_of_df = {}
        keyss = table.keys()
        for t, key in enumerate(keyss):
            key_name = 'table_'+str(t)
            df=pd.DataFrame(table[key])
            dict_of_df[key_name] = copy.deepcopy(df)
        keys = dict_of_df.keys()
        df_total = pd.DataFrame()
        for key in keys:
            df = dict_of_df[key]
            try:
                df.columns = df.iloc[0]
                df = df[1:]
                col = list(df.columns)
                col_lower = [column.lower() for column in df.columns]
                new_col = []
                flag = 0
                flag_unit = 0
                if "Rate" in col and "Amount" in col:
                    for i in range(len(col)-1):
                        if "amount" in col[i].lower():
                            col_name = col[i]
                            df = df.drop(col_name, axis=1)
                            col = list(df.columns)
                if "Item" in col and "Description" in col:
                    for i in range(len(col)-1):
                        if "item" in col[i].lower():
                            col_name = col[i]
                            df = df.drop(col_name, axis=1)
                            col = list(df.columns)
                count_qty = 0
                for i in range(len(col)-1):
                    if "qty" in col[i].lower() or "quantity" in col[i].lower():
                        count_qty = count_qty + 1
                if count_qty > 1:
                    while count_qty > 1:
                        for i in range(len(col)-1):
                            if "qty" in col[i].lower() or "quantity" in col[i].lower():
                                col_name = col[i]
                                df = df.drop(col_name, axis=1)
                                col = list(df.columns)
                                count_qty = count_qty - 1
                for i in range(len(col)-1):
                    if "qty" in col[i].lower() or "quantity" in col[i].lower():
                        col[i] = "Quantity"
                        flag = 1
                    elif "description" in col[i].lower() or "desc" in col[i].lower() or "item" in col[i].lower() or "product" in col[i].lower() or "name" in col[i].lower() or "particular" in col[i].lower():
                        col[i] = "Description"
                    elif "unit" == col[i].lower() or "rate" == col[i].lower() or "unit price" == col[i].lower() or "price" == col[i].lower() or "charge" in col[i].lower() or "unit amount" in col[i].lower():
                        col[i] = "UnitAmount"
                        flag_unit = 1
                    elif "amount" in col[i].lower() and flag_unit == 0:
                        col[i] = "UnitAmount"
                        flag_unit = 1
                df.columns = col
                if (flag == 0):
                    df = df.assign(Quantity=1.0)
                if (flag_unit == 0):
                    df = df.assign(UnitAmount=1.0)   
                df_new = df[["Description","Quantity","UnitAmount"]]
                df_new = df_new[~df_new.apply(lambda row: (row[0].strip() == '' and row[1].strip() == ''), axis=1)]
                df_new['Quantity'] = df_new['Quantity'].apply(lambda x: extract_number(str(x)) if not str(x).isdigit() else x)
                df_new['UnitAmount'] = df_new['UnitAmount'].apply(lambda x: extract_number(str(x)) if not str(x).isdigit() else x)
                df_new = df_new[df_new['UnitAmount'].apply(lambda x: is_number(x))]
                df_new['UnitAmount'] = pd.to_numeric(df_new['UnitAmount'], errors='coerce')
                df_new['Quantity'] = pd.to_numeric(df_new['Quantity'], errors='coerce')
                quantities = df_new['Quantity'].astype(float)
                df_new['Quantity'] = quantities
                for index, row in df_new.iterrows():
                    df_new.loc[index, 'TotalAmount'] = float(row['Quantity']) * float(row['UnitAmount'])
                df_total = pd.concat([df_total,df_new],axis=0)
                
            except Exception as e:
                print("Not a suitable table")
        if(df_total.empty == False):
            return df_total
        else:
            return None

def date_formatter(date):
    try:
        if re.findall(r'\d{1,2}-\d{1,2}-\d{4}', date):
            try:
                dt = datetime.strptime(date,"%d-%m-%Y")
                format_date = dt.strftime("%Y-%m-%d")
            except:
                dt = datetime.strptime(date,"%m-%d-%Y")
                format_date = dt.strftime("%Y-%m-%d")
        elif re.findall(r'\d{1,2}/\d{1,2}/\d{4}', date):
            try:
                dt = datetime.strptime(date,"%d/%m/%Y")
                format_date = dt.strftime("%Y/%m/%d")
            except:
                dt = datetime.strptime(date,"%m/%d/%Y")
                format_date = dt.strftime("%Y/%m/%d")
        elif re.findall(r'\d{1,2} \d{1,2} \d{4}', date):
            try:
                dt = datetime.strptime(date,"%d %m %Y")
                format_date = dt.strftime("%Y %m %d")
            except:
                dt = datetime.strptime(date,"%m %d %Y")
                format_date = dt.strftime("%Y %m %d")
        elif re.findall(r'\d{4}-\d{1,2}-\d{1,2}', date):
            dt = datetime.strptime(date,"%Y-%m-%d")
            format_date = dt.strftime("%Y-%m-%d")
        elif re.findall(r'\d{4}/\d{1,2}/\d{1,2}', date):
            dt = datetime.strptime(date,"%Y/%m/%d")
            format_date = dt.strftime("%Y/%m/%d")
        elif re.findall(r"\d{1,2} [A-Z][a-z][a-z] \d{4}",date):
            dt = datetime.strptime(date,"%d %b %Y")
            format_date = dt.strftime("%Y %m %d") 
        elif re.findall(r"\d{1,2}-[A-Z][a-z][a-z]-\d{4}",date):
            dt = datetime.strptime(date,"%d-%b-%Y")
            format_date = dt.strftime("%Y-%m-%d")
        elif re.findall(r"\d{1,2} [A-Z][a-z][a-z] \d{4}",date):
            dt = datetime.strptime(date,"%d %b %Y")
            format_date = dt.strftime("%Y %m %d")
        elif re.findall(r"\d{1,2} [A-Z][A-Z][A-Z] \d{4}",date):
            dt = datetime.strptime(date,"%d %b %Y")
            format_date = dt.strftime("%Y %m %d")
        elif re.findall(r"\d{1,2}-[A-Z][A-Z][A-Z]-\d{4}",date):
            dt = datetime.strptime(date,"%d-%b-%Y")
            format_date = dt.strftime("%Y-%m-%d")
        elif re.findall(r"\d{1,2}(?:th|st|nd|rd) [A-Z][a-z][a-z] \d{4}",date):
            match = re.search(r"(\d{2})[a-z][a-z] ([A-Z][a-z][a-z]) (\d{4})", date)
            if match:
                day = match.group(1)
                year = match.group(3)
                month = match.group(2)
                date = day + " " + month + " " +year
                print(date)
            dt = datetime.strptime(date,"%d %b %Y")
            format_date = dt.strftime("%Y %m %d")
        elif re.findall(r"\d{1,2}(?:th|st|nd|rd) [A-Z][A-Z][A-Z] \d{2}",date):
            match = re.search(r"(\d{2})[a-z][a-z] ([A-Z][A-Z][A-Z]) (\d{2})", date)
            if match:
                day = match.group(1)
                year = match.group(3)
                month = match.group(2)
                date = day + " " + month + " " + "20"+year
            dt = datetime.strptime(date,"%d %b %Y")
            format_date = dt.strftime("%Y %m %d")
        elif re.findall(r"\d{1,2}(?:th|st|nd|rd) [A-Z][a-z][a-z] \d{2}",date):
            match = re.search(r"(\d{2})[a-z][a-z] ([A-Z][a-z][a-z]) (\d{2})", date)
            if match:
                day = match.group(1)
                year = match.group(3)
                month = match.group(2)
                date = day + " " + month + " " + "20"+year
            dt = datetime.strptime(date,"%d %b %Y")
            format_date = dt.strftime("%Y %m %d")
        elif re.findall(r"\d{1,2}(?:th|st|nd|rd)-[A-Z][A-Z][A-Z]-\d{4}",date):
            dt = datetime.strptime(date,"%d-%b-%Y")
            format_date = dt.strftime("%Y-%m-%d")
        elif re.findall(r"\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}",date):
            dt = datetime.strptime(date,"%d %B %Y")
            format_date = dt.strftime("%Y %m %d")
        elif re.findall(r"\d{1,2}-(?:January|February|March|April|May|June|July|August|September|October|November|December)-\d{4}",date):
            dt = datetime.strptime(date,"%d-%B-%Y")
            format_date = dt.strftime("%Y-%m-%d")
        elif re.findall(r"\d{1,2}(?:th|st|nd|rd) (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{2}",date):
            match = re.search(r"(\d{2})[a-z][a-z] (?:January|February|March|April|May|June|July|August|September|October|November|December) (\d{2})", date)
            if match:
                day = match.group(1)
                year = match.group(3)
                month = match.group(2)
                date = day + " " + month + " " + "20"+year
            dt = datetime.strptime(date,"%d %B %Y")
            format_date = dt.strftime("%Y %m %d")
        elif re.findall(r"\d{1,2}-[A-Z][a-z][a-z]-\d{2}",date):
            match = re.search(r"(\d{2})-([A-Z][a-z][a-z])-(\d{2})", date)
            if match:
                day = match.group(1)
                year = match.group(3)
                month = match.group(2)
                date = day + " " + month + " " + "20"+year
            dt = datetime.strptime(date,"%d %b %Y")
            format_date = dt.strftime("%Y %m %d") 
        else:
            format_date = date
    except:
        format_date = date
    return format_date

def query_to_json(query_answers):
    print(query_answers)
    if('COMPANY_NAME' in query_answers.keys()):
        company_name = query_answers['COMPANY_NAME']
    else:
        company_name = ""
    if('COMPANY_ADDRESS' in query_answers.keys()):
        company_address = query_answers['COMPANY_ADDRESS']
    else:
        company_address = ""
    if('RECEIVER_NAME' in query_answers.keys()):
        receiver_name = query_answers['RECEIVER_NAME']
    else:
        receiver_name = ""
    if('RECEIVER_ADDRESS' in query_answers.keys()):
        receiver_address = query_answers['RECEIVER_ADDRESS']
    else:
        receiver_address = ""
    if('INVOICE_DATE' in query_answers.keys()):
        invoice_date = date_formatter(query_answers['INVOICE_DATE'])
    else:
        invoice_date = ""
    if('DUE_DATE' in query_answers.keys()):
        due_date = date_formatter(query_answers['DUE_DATE'])
    else:
        due_date = ""
    if('INVOICE_NO' in query_answers.keys()):
        invoice_no = query_answers['INVOICE_NO']
    else:
        if(invoice_date!=""):
            invoice_no = invoice_date
        elif(due_date!=""):
            invoice_no = due_date
        else:
            invoice_no = ""
    if('SUB_TOTAL' in query_answers.keys()):   
        sub_total = float(extract_numbers(query_answers['SUB_TOTAL'])[0])
    else:
        sub_total = 0
    if('DISCOUNT' in query_answers.keys()):   
        discount = float(extract_numbers(query_answers['DISCOUNT'])[0])
    else:
        discount = 0
    if('TAX_PERCENT' in query_answers.keys()):   
        taxper = float(extract_numbers(query_answers['TAX_PERCENT'])[0])
    else:
        taxper = ""
    if('TOTAL' in query_answers.keys()):   
        total = float(extract_numbers(query_answers['TOTAL'])[0])
    else:
            total = 0
    if('TAX_AMOUNT' in query_answers.keys()):
        if("%" in query_answers['TAX_AMOUNT']):
            tax_percent = float(extract_numbers(query_answers['TAX_AMOUNT'])[0])
            if(sub_total!=0):
                tax_amount = (tax_percent*sub_total)/100
            else:
                tax_amount = (tax_percent*total)/100
        else:
            tax_percent = 10
            tax_amount = float(extract_numbers(query_answers['TAX_AMOUNT'])[0])
    else: 
        tax_amount = 0
        tax_percent=10
    if(total == 0 and sub_total!=0):
        total = sub_total +tax_amount
    if(company_name):
        closest_comp_name = find_company_match(company_name.lower())
        if(closest_comp_name):
            acc_all_type = find_account_code(closest_comp_name)
        else:
            acc_all_type = ""
    else:
        acc_all_type = ""
    if(sub_total!=0 and tax_amount!=0 and round(0.1*sub_total,2)==tax_amount and sub_total+tax_amount == total):
        taxable_amount = sub_total
        non_taxable_amount = 0
    elif((tax_amount!=0 and tax_amount !='') and total!=0):
        taxable_amount = round((tax_amount*100)/tax_percent, 3)
        if (taxable_amount + tax_amount) == total or total - (taxable_amount + tax_amount)  <= 0.01:
            non_taxable_amount = 0
        else:
            non_taxable_amount = round(total - taxable_amount,2)
    elif (tax_amount==0 or tax_amount =='') and total!=0:
        non_taxable_amount = total
        taxable_amount = 0.0
    else: 
        non_taxable_amount = 0.0
        taxable_amount = 0.0
    obj = { "invoice_from": {"name": company_name, "address": company_address},
            "invoice_to": {"name": receiver_name, "address": receiver_address},
            "invoice_date": invoice_date,
            "invoice_no": invoice_no,
            "due_date": due_date,
            "tax_rate": tax_percent,
            "Sub Total": sub_total,
            "Total Bill Amount": total,
            "Tax Amount": tax_amount,
            "Tax Percent": taxper,
            "Discount": discount,
            "line_items": {"0":{"Description": company_name,"Quantity": 1.0 ,"UnitAmount": taxable_amount, "Tax Type":"Tax Applicable","Account Type": acc_all_type,"TotalAmount": taxable_amount},
            "1":{"Description": company_name,"Quantity": 1.0 ,"UnitAmount": non_taxable_amount, "Tax Type":"Tax Not Applicable", "Account Type": acc_all_type, "TotalAmount": non_taxable_amount}}
          }
    
    y = json.dumps(obj)
    print(y)
    return y
        
