from flask import Blueprint,render_template,request,flash,redirect,url_for,session,Flask, redirect
from .models import User
import os 
import base64
import requests
from datetime import datetime, timedelta
from .utils import update_new_access_token_using_refresh
from pymongo import MongoClient 
client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client[f"{os.getenv('db_name')}"]
mycollection = mydatabase['users']  
uploads=mydatabase["uploads"]
from dotenv import load_dotenv
load_dotenv()

user_control=Blueprint("manage-user",__name__)

@user_control.route("/manage-user")
def choose_user_option():
    if 'user' in session:
        if session["role"]=='Admin':
            all_data=mycollection.find()
            # print(all_data)
            data=[]
            for i in all_data:
                print(i["user"],"")
                data.append(i)
            return render_template("manage-users.html",data=data)
        else:
            return redirect(url_for("auth.login"))
    else:
        return redirect(url_for('auth.login'))
@user_control.route(rule="/manage-companies",methods=["GET","POST"])
def manage_user():
    if "user" in session:
        if request.method=="POST":
            try:
                company=request.form["company"]
            except KeyError as e:
                flash("please select a company")
                print(e)
                return redirect(url_for('manage-user.manage_user'))
            print(company,"this is company")
            session["company"]=company
            return redirect(url_for('bills.create_bill_page'))
        else:
            try:
                if "user" in session:
                # if session["role"]=="Admin":
                    url = 'https://api.xero.com/connections'
                    current_time_stamp=datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
                    mongo_data=mycollection.find_one({"user":session["user"]})
                    if current_time_stamp>mongo_data['access_expired_time']:
                        update_new_access_token_using_refresh(session["user"],mongo_data["refresh_token"])
                        mongo_data=mycollection.find_one({"user":session["user"]})
                    headers = {
                        'Authorization': 'Bearer ' + mongo_data["access_token"],
                        'Content-Type': 'application/json'
                    }

                    resp = requests.get(url=url, headers=headers)

                    if resp.status_code == 200:
                        print("success in gettting data")
                        print(resp.json(),"this is json response")
                        User.add_tenant_to_profile(user=session["user"],tenant_list=resp.json())
                        print("tenant data added sucessfully")
                        for i in resp.json():
                            if i:
                                print(i["tenantName"],"tenant name printing")
                    mongo_data_for_tenant=mycollection.find_one({"user":session["user"]})
                    company_list=mongo_data_for_tenant["tenant_list"]
                    company_name_list=[]
                    if company_list:
                        # print(company_list,"this is company list")
                        for tenant_list in company_list:
                            print(tenant_list["tenantName"],"single tenant")
                            company_name_list.append({"tenat_name":tenant_list["tenantName"],"tenant_mail":mongo_data_for_tenant["email"]})
                    return render_template('manage-tenant.html',companies=company_name_list)
            except Exception as e:
                print(e)
                return {"data":"role not allowed"}
            return render_template("users_manage/manage_companies.html")