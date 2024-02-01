from flask import Blueprint,render_template,request,session,redirect,url_for
import boto3
import os
from pymongo import MongoClient 

views=Blueprint("views",__name__)

bucket_name=os.getenv("bucket_name")
aws_access_key=os.getenv("Access_key_ID")
aws_secret_key=os.getenv("Secret_access_key")
region=os.getenv("region")

client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client[f"{os.getenv('db_name')}"]
mycollection = mydatabase['users']  
uploads=mydatabase["uploads"]


s3 = boto3.client('s3',aws_access_key_id=aws_access_key,aws_secret_access_key=aws_secret_key)


@views.route(rule="/")
@views.route(rule="/dashboard")
def dashboard():
    if "user" in session :
        if session["role"]=="Admin":
            mongo_data=uploads.find()
        elif session["role"]=="User":
            user=session["user"]
            mongo_data=uploads.find({"user":user})
        
        created_data=[]
        in_progress_data=[]
        pending_approval_data=[]
        approved_data=[]
        rejected_data=[]
        for i in mongo_data:
            if i["status"]=="Created":
                created_data.append(i)
            elif i["status"]=="In-progress":
                in_progress_data.append(i)
            elif i["status"]=="Pending":
                pending_approval_data.append(i)
            elif i["status"]=="Approved":
                approved_data.append(i) 
            elif i["status"]=="Rejected":
                rejected_data.append(i)
        all_data_from_mongo=len(created_data)+len(in_progress_data)+len(pending_approval_data)+len(approved_data)+len(rejected_data)
        donut_data={
            'labels':["Created","In-progress","Pending","Approved","Rejected"],
            'data':[len(created_data),len(in_progress_data),len(pending_approval_data),len(approved_data),len(rejected_data)],
            'backgroundColor': ['rgba(88, 86, 214, 1)', 'rgba(255, 149, 0, 1)', 'rgba(255, 214, 49, 1)','rgba(52, 199, 89, 1)','rgba(255, 59, 48, 1)'],
            'hoverBackgroundColor': ['rgba(65, 62, 213, 1)', 'rgba(183, 110, 6, 1)', 'rgba(227, 186, 22, 1)','rgba(7, 159, 45, 1)','rgba(251, 46, 34, 1)'],
        }
        donut_data_created={
            'labels':['Created',"Total"],
            'data':[len(created_data),all_data_from_mongo],
            'backgroundColor':['rgba(88, 86, 214, 1)',"rgba(0, 0, 0, 0.15)"],
            'hoverBackgroundColor':['rgba(65, 62, 213, 1)',"rgba(0, 0, 0, 0.3)"]
        }
        donut_data_in_progress={
            'labels':['In-Progress',"Total"],
            'data':[len(in_progress_data),all_data_from_mongo],
            'backgroundColor':['rgba(255, 149, 0, 1)',"rgba(0, 0, 0, 0.15)"],
            'hoverBackgroundColor':['rgba(183, 110, 6, 1)',"rgba(0, 0, 0, 0.3)"]
        }
        donut_data_pending={
            'labels':['Pending',"Total"],
            'data':[len(pending_approval_data),all_data_from_mongo],
            'backgroundColor':['rgba(255, 214, 49, 1)',"rgba(0, 0, 0, 0.15)"],
            'hoverBackgroundColor':['rgba(227, 186, 22, 1)',"rgba(0, 0, 0, 0.3)"]
        }
        donut_data_approved={
            'labels':['Approved',"Total"],
            'data':[len(approved_data),all_data_from_mongo],
            'backgroundColor':['rgba(52, 199, 89, 1)',"rgba(0, 0, 0, 0.15)"],
            'hoverBackgroundColor':['rgba(7, 159, 45, 1)',"rgba(0, 0, 0, 0.3)"]
        }
        donut_data_rejected={
            'labels':['Rejected',"Total"],
            'data':[len(rejected_data),all_data_from_mongo],
            'backgroundColor':['rgba(255, 59, 48, 1)',"rgba(0, 0, 0, 0.15)"],
            'hoverBackgroundColor':['rgba(251, 46, 34, 1)',"rgba(0, 0, 0, 0.3)"]
        }
        data={"Created":created_data,"In-progress":in_progress_data,"Pending":pending_approval_data,"Approved":approved_data,"Rejected":rejected_data}    
        
        return render_template("index.html",donut_data_created=donut_data_created,donut_data_in_progress=donut_data_in_progress,donut_data_pending=donut_data_pending,donut_data_approved=donut_data_approved,donut_data_rejected=donut_data_rejected,over_all_donut_data=donut_data,bar_data=donut_data)
    elif "user" in session:
        mongo_data=uploads.find({"user":session["user"]})
        data=[]
        for i in mongo_data:
            data.append(i)
        # print(data,"user data from mongo uploads",session["user"])
        return render_template("dashboard.html",data=data,user_name=session["user"])
    else:
        return redirect(url_for("auth.login"))

