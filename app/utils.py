import requests
import os
import base64
import requests
from .models import User
from flask import session,redirect,url_for
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import session,request
load_dotenv()
from pymongo import MongoClient 
client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client[f"{os.getenv('db_name')}"]
mycollection = mydatabase['users']  
uploads=mydatabase["uploads"]

b64_secret = base64.b64encode(bytes(os.getenv('client_id') + ':' + os.getenv('client_secret'), 'utf-8')).decode('utf-8')


#Updating a new access token with a existing refresh token and save it in DB
def update_new_access_token_using_refresh(user,refresh_token):
    url = 'https://identity.xero.com/connect/token'
    headers = {'Authorization': 'Basic ' + b64_secret, }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    resp = requests.post(url=url, headers=headers, data=data)
    print(resp)
    if resp.status_code == 200:
        access_token=resp.json()["access_token"]
        refresh_token=resp.json()['refresh_token']
        session['access_token']=access_token
        access_expired_time=(datetime.utcnow() + timedelta(minutes=6)).strftime('%Y%m%d%H%M%S%f')
        new_data={'access_token':access_token, 'refresh_token': refresh_token,"access_expired_time":access_expired_time}
        # print( resp.json())
        try:
            mycollection.update_one({'user':user}, {'$set': new_data}, upsert=True)
            print("Successfully updated new access token...")
        except:
            print("Error in updating new access token....")
    else:
        print("No data found...")



# update_new_access_token_using_refresh("Admin","RpNjcYAh3R2dWK3ycUOJVqGWaMUr6f3m7OsVI1rUWLc")
# def check_mongo_and_update():
#     mongo_data=mycollection.find_one({"user":"Admin"})
#     current_time_stamp=datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
#     expire_time_stamp=mongo_data["access_expired_time"]
#     if current_time_stamp>expire_time_stamp:
#         #just for testing purpose remove after test
#         update_new_access_token_using_refresh("Admin","RpNjcYAh3R2dWK3ycUOJVqGWaMUr6f3m7OsVI1rUWLc")
#         print("current mongo token has expired so updated new token..")
#     else:
#         print("current access token is valid ")
# check_mongo_and_update()
def get_organisation_api_data(access, tenant):
    url = 'https://api.xero.com/api.xro/2.0/Organisation'
    mongo_data=mycollection.find_one({"user":session["user"]})
    current_time_stamp=datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    expire_time_stamp=mongo_data["access_expired_time"]
    if current_time_stamp>expire_time_stamp:
        #just for testing purpose remove after test
        update_new_access_token_using_refresh(session["user"],mongo_data["refresh_token"])
        print("current mongo token has expired so updated new token..")
    else:
        print("current access token is valid ")
    access=mongo_data["access_token"]
    headers = {
        'Authorization': 'Bearer ' + access,
        'Xero-tenant-id': tenant,
        'Accept': 'application/json',
    }
    resp = requests.get(url=url, headers=headers)

    if resp.status_code == 200:
        for i in resp.json():
            print(i)
            print()

    print((f'{resp.json()}', 'danger'))
    return []

# get_organisation_api_data(access=access,tenant='1665af03-db78-4321-85df-d775a2f999a2')
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
            return None

def get_tenant_api_data(access):
    # update tenants
    url = 'https://api.xero.com/connections'
    headers = {
        'Authorization': 'Bearer ' + access,
        'Content-Type': 'application/json'
    }
    resp = requests.get(url=url, headers=headers)

    if resp.status_code == 200:
        return resp.json()

    # print(f'{resp.json()}', 'danger')
    return resp.json()
def get_supplier_using_name(user,current_company,supplier_name):
    mongo_data=mycollection.find_one({"user":user})
    current_time_stamp=datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    if "company" not in session:
        redirect(url_for("manage-user.manage_user"))
    if current_time_stamp>mongo_data['access_expired_time']:
        print("access session time out")
        update_new_access_token_using_refresh(user,mongo_data["refresh_token"])
        print("access refreshed")
        mongo_data=mycollection.find_one({"user":user}) 
    print("now access token valid")
    if "company" in session:
        print(session["company"])
        tenant_list=mycollection.find_one({"user":user})
        tenant_id_list=[]
        if 'access_token' not in session:
            redirect(url_for('x_auth.get_code_for_access'))
        for tenant in tenant_list["tenant_list"]:
            if tenant['tenantName']==current_company:
                print("current company is selected")
                tenant_id=tenant["tenantId"]
                break
        url = 'https://api.xero.com/api.xro/2.0/Contacts'
        headers = {
                'Authorization': 'Bearer ' + session["access_token"],
                'Xero-tenant-id': tenant_id,
                'Accept': 'application/json',}
        
        resp = requests.get(url=url, headers=headers)
        if resp.status_code == 200:
            supplier_list=[]
            response_data=resp.json()
            for data in response_data:
                if data=="Contacts":
                    for j in resp.json()[data]:
                        supplier_list.append({j["Name"]:j["ContactID"]})
            for name in supplier_list:
                for name_in_dict in name:
                    if name_in_dict==supplier_name:
                        supplier_id=name[name_in_dict]
                        return supplier_id

                   
def get_supplier_list(user,current_company):
        mongo_data=mycollection.find_one({"user":user})
        current_time_stamp=datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        if "company" not in session:
            redirect(url_for("manage-user.manage_user"))
        if current_time_stamp>mongo_data['access_expired_time']:
            print("access session time out")
            update_new_access_token_using_refresh(user,mongo_data["refresh_token"])
            print("access refreshed")
            mongo_data=mycollection.find_one({"user":user}) 
        print("now access token valid")
        if "company" in session:
            print(session["company"])
            tenant_list=mycollection.find_one({"user":user})
            tenant_id_list=[]
            if 'access_token' not in session:
                redirect(url_for('x_auth.get_code_for_access'))
            for tenant in tenant_list["tenant_list"]:
                if tenant['tenantName']==current_company:
                    print("current company is selected")
                    tenant_id=tenant["tenantId"]
                    break
            url = 'https://api.xero.com/api.xro/2.0/Contacts'
            headers = {
                    'Authorization': 'Bearer ' + session["access_token"],
                    'Xero-tenant-id': tenant_id,
                    'Accept': 'application/json',}
            
            resp = requests.get(url=url, headers=headers)
            if resp.status_code == 200:
                supplier_list=[]
                response_data=resp.json()
                for data in response_data:
                    if data=="Contacts":
                        for j in resp.json()[data]:
                            supplier_list.append({j["Name"]:j["ContactID"]})
                        return supplier_list