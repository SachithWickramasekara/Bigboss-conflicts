import os
from flask import session
from flask_bcrypt import Bcrypt
import base64
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv
load_dotenv()
from pymongo import MongoClient 
client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client[f"{os.getenv('db_name')}"]
mycollection = mydatabase['users']  
uploads=mydatabase["uploads"]
bcrypt = Bcrypt()
b64_secret = base64.b64encode(bytes(os.getenv('client_id') + ':' + os.getenv('client_secret'), 'utf-8')).decode('utf-8')

class User():

    #Create a login requried function for mongo
    def login_user(self,email,password):
        try:
            user_data=mycollection.find_one({"email":email})
            print("GOT USER DATA")
            print(user_data)
            # print(user_data["password"],'mongo data password')
            # print(password,"user typed password")
            if user_data and user_data["password"]:
                print("ABOUT TO CHECK")
                if bcrypt.check_password_hash(user_data['password'],password):
                    print("PASSWORD VERIFIED")
                    session.clear()
                    session["user"]=user_data["user"]
                    session["role"]=user_data["role"]
                    return {'data':{"user":user_data["user"],'role':user_data["role"]},'error':False}
                else :return {'data':{"user":None,'role':None},'error':True}
            else:return {'data':{"No data found"},'error':True}
        except Exception as e:
            print("error : ",e)
    def sign_up_user(data):
        try:
            print("preparing to sign up..")
            hashed_password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')
            data["password"]=hashed_password
            mycollection.insert_one(data)
            print(f"{data['user']} has been signed up...")
        except:
            print("error in signing up...")
    #clogout user with session cleared
    def logout_user(self):
        try:
            if session["user"]:
                session.clear()
                return {'data':{"user loged out."},'error':False}
            else:
                return {'data':{"user not found."},'error':False}
        except Exception as e:
            return {'data':{"No data found"},'error':True}
        
    #Create a new access token and refresh token for the first time and save it in DB
    def add_new_token(user,access_token,refresh_token):
        try:
            if access_token!=None and refresh_token!=None:
                access_expired_time=(datetime.utcnow() + timedelta(minutes=6)).strftime('%Y%m%d%H%M%S%f')
                new_data = {'access_token':access_token, 'refresh_token': refresh_token,"access_expired_time":access_expired_time}
                try:
                    mycollection.update_one({'user':user}, {'$set': new_data}, upsert=True)
                    print("update sucessfull")
                except:
                    print("error in updating....")
        except:
            print("no data found please try again")
    def add_tenant_to_profile(user,tenant_list):
        try:
            if len(tenant_list)>=1:
                new_data={"tenant_list":tenant_list}
                mycollection.update_one({'user':user}, {'$set': new_data})
                print("tenant updated")
        except Exception as e:
            print(e)
            print('error in updating tenant list')





    
