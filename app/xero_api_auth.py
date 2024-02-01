from flask import Blueprint,render_template,request,flash,redirect,url_for,session,Flask, redirect
from .models import User
from requests_oauthlib import OAuth2Session
import os 
import base64
import requests
import json
import ast
import boto3
from io import BytesIO
from datetime import datetime, timedelta
from .utils import update_new_access_token_using_refresh , get_supplier_list ,get_supplier_using_name
from pymongo import MongoClient 
client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client[f"{os.getenv('db_name')}"]
mycollection = mydatabase['users']  
uploads=mydatabase["uploads"]
from dotenv import load_dotenv
load_dotenv()
bucket_name=os.getenv("bucket_name")
aws_access_key=os.getenv("Access_key_ID")
aws_secret_key=os.getenv("Secret_access_key")
region=os.getenv("region")
x_auth=Blueprint("x_auth",__name__)
b64_secret = base64.b64encode(bytes(os.getenv('client_id') + ':' + os.getenv('client_secret'), 'utf-8')).decode('utf-8')
s3 = boto3.client('s3',aws_access_key_id=aws_access_key,aws_secret_access_key=aws_secret_key)

@x_auth.route(rule="/login",methods=["GET","POST"])
def get_first_auth_token():
    if "user" in session:
        auth_url = "https://login.xero.com/identity/connect/authorize"
        auth_params = {
        'client_id': os.getenv('client_id'),
        'response_type': 'code',
        'redirect_uri': os.getenv('redirect_uri'),
        'scope':'offline_access openid profile email accounting.transactions accounting.settings accounting.contacts accounting.attachments'
                
        # 'scope': 'openid profile email accounting.transactions offline_access',
        }
        authurazation_url = f"{auth_url}?{'&'.join([f'{key}={value}' for key, value in auth_params.items()])}"
        return redirect(authurazation_url)
    else :
        return redirect(url_for('auth.login'))
    
@x_auth.route(rule="/")
def get_code_for_access():
    if 'user' in session:

        data=request.args.get('code')
        url = 'https://identity.xero.com/connect/token'
        headers = {'Authorization': 'Basic ' + b64_secret}
        data = {
            'grant_type': 'authorization_code',
            'code': data,
            'redirect_uri': os.getenv("redirect_uri")
        }

        resp = requests.post(url=url, headers=headers, data=data)
        # print('***AUTH API***\n', resp.json(), '\n\n')
        
        if resp.status_code == 200:
            access_token=resp.json()["access_token"]
            refresh_token=resp.json()["refresh_token"]
            session["access_token"]=access_token
            User.add_new_token(session["user"],access_token,refresh_token)
            return redirect(url_for("x_auth.get_tenant"))

    else:
        return redirect(url_for('auth.login'))

@x_auth.route(rule="/get-tenant")
def get_tenant():
    if 'user' in session:
        url = 'https://api.xero.com/connections'
        current_time_stamp=datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        mongo_data=mycollection.find_one({"user":session["user"]})
        # print(mongo_data)

        #check access token is valid if not valid it just updating the token
        try:
            if current_time_stamp>mongo_data['access_expired_time']:
                update_new_access_token_using_refresh(session["user"],mongo_data["refresh_token"])
                mongo_data=mycollection.find_one({"user":session["user"]})
            headers = {
                'Authorization': 'Bearer ' + mongo_data["access_token"],
                'Content-Type': 'application/json'
            }

            resp = requests.get(url=url, headers=headers)

            if resp.status_code == 200:
                print(resp.json())
                print("success in gettting data")
                User.add_tenant_to_profile(user=session["user"],tenant_list=resp.json())
                print("tenant data added sucessfully")
                for i in resp.json():
                    if i:
                        print(i["tenantName"])
                return redirect(url_for('manage-user.manage_user'))
        except Exception as e:
            print(e)
            return redirect(url_for("x_auth.get_first_auth_token"))
    else:
        return redirect(url_for("auth.login"))
            

@x_auth.route(rule="/Invoice",methods=["POST"])
def post_invoice():
    invoice_number=request.form['bill_num']
    doc_name=request.form['doc_name']
    bill_date=request.form['bill_date']
    bill_date=bill_date.replace(" ","/")
    account_type=request.form["account_type"]
    print(bill_date, 'this is bill date')
    due_date=request.form['due_date']
    due_date=due_date.replace(" ","/")
    print(due_date,"this is due date")
    get_description=request.form.getlist('description')
    get_account=request.form.getlist('account')
    get_quantity=request.form.getlist('quantity')
    get_tax_type=request.form.getlist('tax_type')
    get_total_ammout=request.form.getlist('total_amount')
    get_unit_price=request.form.getlist('unit_price')
    get_supplier_id=request.form['supplier']
    try:
        get_supplier_id=ast.literal_eval(get_supplier_id)
        print(get_supplier_id,type(get_supplier_id))
        supplier_id="".join(get_supplier_id.values())
        print(supplier_id,type(supplier_id),"this is supplier id")
    except:
        print("working on supplier id")
        supplier_id=get_supplier_using_name(session['user'],session['company'],get_supplier_id)
        print(supplier_id,"this is new supplier id")
    print(supplier_id,"this is supplier id")
    #make quantity as number
    user_data=mycollection.find_one({'user':session['user']})
    over_all_data=[]
    for j in user_data["tenant_list"]:
            if j["tenantName"]==session["company"]:
                print("inside for loop for create suppliers")
                tenant_id=j['tenantId']
                print(tenant_id)
    for i in range(len(get_description)):
        data_row={}
        data_row["Description"]=get_description[i]
        # data_row["account"]=get_account[i]
        data_row['Quantity']=get_quantity[i]
        data_row['AccountCode']=get_tax_type[i]
        # data_row['total_amount']=get_total_ammout[i]
        data_row['UnitAmount']=get_unit_price[i]
        over_all_data.append(data_row)
    
    invoice_data = {
    "Type": account_type,  # Accounts payable
    "Contact": {
        "ContactID": supplier_id  # Replace with an existing contact ID or create a new contact
    },
    "Date": due_date,#replace with line action
    "DueDate": due_date, 
    "InvoiceNumber":invoice_number, # Adjust due date as needed
    "LineItems" : over_all_data
    }
    data = json.dumps(invoice_data) 
    current_time_stamp=datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    mongo_data=mycollection.find_one({"user":session["user"]})
    if current_time_stamp>mongo_data['access_expired_time']:
        update_new_access_token_using_refresh(session["user"],mongo_data["refresh_token"])
    
    url = 'https://api.xero.com/api.xro/2.0/Invoices'
    headers = {
        'Authorization': 'Bearer ' + session['access_token'],
        'Xero-tenant-id': tenant_id,
        'Accept': 'application/json',
    }
    resp = requests.post(url=url, headers=headers, data=data)
    print(resp.content)
    if resp.status_code==200 and session['role']=="Admin":
        resp_json=resp.json()
        print(resp.json())
        xero_invoice_id=resp_json['Invoices'][0]['InvoiceID']
        uploads.update_one({'document_name':doc_name},{'$set':{'status':"Approved","xero_invoice_id":xero_invoice_id}})
        print(resp.status_code,"posted on xero")
        current_time_stamp=datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        mongo_data=mycollection.find_one({"user":session["user"]})
        if current_time_stamp>mongo_data['access_expired_time']:
            update_new_access_token_using_refresh(session["user"],mongo_data["refresh_token"])
        file_name=uploads.find_one({"document_name":doc_name})['file_name']
        url = f"https://api.xero.com/api.xro/2.0/Invoices/{xero_invoice_id}/Attachments/{file_name}"
        data=s3.get_object(Bucket=bucket_name,Key=f'PROCESSED/{doc_name}/{file_name}')
        image_data_byte=data["Body"].read()
        data=base64.b64encode(image_data_byte).decode("utf-8")
        if file_name.endswith(".jpeg"):
            headers = {
            'Authorization': 'Bearer ' + session['access_token'],
            'Xero-tenant-id': tenant_id,
            'Accept': 'application/json',
            'Content-Type': 'image/jpeg',
            'ContentLength': str(len(image_data_byte)),
            'MimeType':'image/jpeg',
            }
        elif file_name.endswith(".jpg"):
            headers = {
            'Authorization': 'Bearer ' + session['access_token'],
            'Xero-tenant-id': tenant_id,
            'Accept': 'application/json',
            'Content-Type': 'image/jpg',
            'ContentLength': str(len(image_data_byte)),
            'MimeType':'image/jpg',
            }
        elif file_name.endswith(".png"):
            headers = {
            'Authorization': 'Bearer ' + session['access_token'],
            'Xero-tenant-id': tenant_id,
            'Accept': 'application/json',
            'Content-Type': 'image/jpg',
            'ContentLength': str(len(image_data_byte)),
            'MimeType':'image/png',
            }
        print(bucket_name,f'processed/{doc_name}/{file_name}')
        
        # image_stream = BytesIO(image_data_byte)
        # data = open(image_stream, 'rb')
        second_resp = requests.post(url=url, headers=headers, data=data)
        print(second_resp.content)
        print(second_resp.json())
        flash("Xero Upload Successful...",'info')
        return redirect(url_for("queue.my_queue"))
    # elif resp.status_code==200 and session['role']=="User":
    #     uploads.update_one({'document_name':doc_name},{'$set':{'status':"Pending"}})
    #     return redirect(url_for("views.dashboard"))
    else:
        return redirect(url_for('queue.my_queue'))
    # return {"response":str(resp)}

@x_auth.route(rule="/contact-form")
def create_contact_form():
    return render_template("users_manage/create_contact.html")


@x_auth.route(rule="/create-supplier",methods=["POST","GET"])
def create_supplier():
    if 'user' in session :
        if request.method=="POST":
            name=request.form["contact_name"]
            first_name=request.form["first_name"]
            last_name=request.form["last_name"]
            email=request.form["email"]
            tax_number=request.form["tax_number"]
            mongo_data=mycollection.find_one({"user":session["user"]})
            current_time_stamp=datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            if "company" not in session:
                redirect(url_for("manage-companies.manage_user"))
            if current_time_stamp>mongo_data['access_expired_time']:
                print("access session time out")
                update_new_access_token_using_refresh(session["user"],mongo_data["refresh_token"])
                print("access refreshed")
                mongo_data=mycollection.find_one({"user":session["user"]}) 
            print("now access token valid")
            if "company" in session:
                print(session["company"],"in create supplier")
                for i in mongo_data["tenant_list"]:
                    if i["tenantName"]==session["company"]:
                        print("inside for loop for create suppliers")
                        print()
                        tenant_id=i['tenantId']
                        print(tenant_id)
                new_contact_data = {
                    'Name': name,  # Replace with the contact name
                    'FirstName': first_name,
                    'LastName': last_name,
                    'EmailAddress': email,
                    'TaxNumber':tax_number
            # Add other contact details as needed
                                }
                headers = {
                'Authorization': f'Bearer {session["access_token"]}',
                'Xero-tenant-id': tenant_id,
                'Content-Type': 'application/json',
                        }
                url = 'https://api.xero.com/api.xro/2.0/contacts'
                print("abbout to post contact")
                try:
                    resp = requests.post(url=url, headers=headers, data=json.dumps(new_contact_data))
                    print("posted or fails")
                    # print(resp.text,"text")
                    print(resp.headers['Content-Type'])
                    try:
                        json_data = resp.json()
                        # Process the JSON data
                    except json.decoder.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
                    if resp.status_code == 200:
                        print("sucessfull post contact")
                        return redirect(url_for('views.dashboard'))
                    else:
                        print(resp.content,"text contant")
                        return redirect(url_for("bills.create_bill_page"))
                except Exception as e:
                    print(e)
                    
                
            
            else:
                return redirect(url_for('x_auth.get_tenant'))
        else:
            return render_template('create_supplier.html')
    else:
        return redirect(url_for('auth.login'))

@x_auth.route(rule="/get-supplier")
def get_supplier():
    try:
        mongo_data=mycollection.find_one({"user":session["user"]})
        current_time_stamp=datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        if "company" not in session:
            redirect(url_for("manage-companies.manage_user"))
        if current_time_stamp>mongo_data['access_expired_time']:
            print("access session time out")
            update_new_access_token_using_refresh(session["user"],mongo_data["refresh_token"])
            print("access refreshed")
            mongo_data=mycollection.find_one({"user":session["user"]}) 
        print("now access token valid")
        if "company" in session:
            print(session["company"])
            tenant_list=mycollection.find_one({"user":session["user"]})
            for tenant in tenant_list["tenant_list"]:
                if tenant['tenantName']==session["company"]:
                    print("current company is selected")
                    tenant_id=tenant["tenantId"]
                    print(tenant_id,"this is tenant")
                    url = 'https://api.xero.com/api.xro/2.0/Contacts'
                    headers = {
                        'Authorization': 'Bearer ' + session["access_token"],
                        'Xero-tenant-id': tenant_id,
                        'Accept': 'application/json',}
                    resp = requests.get(url=url, headers=headers)
                    print(resp.json(),"this is supplier response")
                    if resp.status_code == 200:
                        supplier_list=[]
                        for data in resp.json():
                            if data=="Contacts":
                                for j in resp.json()[data]:
                                    print(j)
                                    supplier_list.append({j["Name"]:j["ContactID"]})
                                
            return render_template("bills/create_bills.html",supplier=supplier_list)
        else:
            return {"data":"no data found"}
    except Exception as e:
        print(e,"this is reason")
        return {"data":"No data found"}   

@x_auth.route(rule="/get-access")
def get_access_tokens_api():
    #Refresh token and new access token 
    if "user" in session:
        user=session["user"]
        mongo_data=mycollection.find_one({'user':user})
        try:
            refresh=mongo_data["refresh_token"]
        except KeyError:
            return redirect(url_for('x_auth.get_first_auth_token'))

        url = 'https://identity.xero.com/connect/token'
        headers = {'Authorization': 'Basic ' + b64_secret, }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh,
        }

        resp = requests.post(url=url, headers=headers, data=data)

        if resp.status_code == 200:
            new_data_access=resp.json()
            new_data={"access_token":new_data_access['access_token'],"refresh_token":new_data_access["refresh_token"]}
            mycollection.update_one({'user':user}, {'$set': new_data}, upsert=True)
            session["access_token"]=new_data_access['access_token']
            session["refresh_token"]=new_data_access["refresh_token"]
            return redirect(url_for('views.dashboard'))    
    else:
        return redirect(url_for('auth.login'))
@x_auth.route(rule="/get-currency")
def get_currency():
    if "user" in session:
        mongo_data=mycollection.find_one({"user":session["user"]})
        current_time_stamp=datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        if "company" not in session:
            redirect(url_for("manage-companies.manage_user"))
        if current_time_stamp>mongo_data['access_expired_time']:
            print("access session time out")
            update_new_access_token_using_refresh(session["user"],mongo_data["refresh_token"])
            print("access refreshed")
            mongo_data=mycollection.find_one({"user":session["user"]}) 
        print("now access token valid")
        # curr
        if "company" in session:
            print(session["company"])
            tenant_list=mycollection.find_one({"user":session["user"]})
            for tenant in tenant_list["tenant_list"]:
                if tenant['tenantName']==session["company"]:
                    print("current company is selected")
                    tenant_id=tenant["tenantId"]
                    print(tenant_id,"this is tenant")
            url = 'https://api.xero.com/api.xro/2.0/Currencies'
            headers = {
                'Authorization': 'Bearer ' + session['access_token'],
                'Xero-tenant-id': tenant_id,
                'Accept': 'application/json',
            }

            resp = requests.get(url=url, headers=headers)

            if resp.status_code == 200:
                print(resp.json())
                mycollection.update_one({'user':session['user']},{'$set':{"currencies":resp.json()["Currencies"]}})
                # return resp.json()["Currencies"]
                return redirect(url_for('bills.edit_bill'))
            
                # mycollection.update_one({"user":session["user"],'$set':{"currency":}})

    else:
        return redirect(url_for('auth.login'))