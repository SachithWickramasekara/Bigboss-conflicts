from flask import Blueprint,render_template,request,flash,redirect,url_for,session
from .models import User
import datetime
import boto3
import os
import pandas as pd
from pymongo import MongoClient 

client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client[f"{os.getenv('db_name')}"]
mycollection = mydatabase['users']  
uploads=mydatabase["uploads"]
uploads_invoice=mydatabase["uploads_invoice"]
upload_journals=mydatabase["uploads_journals"]


bucket_name=os.getenv("bucket_name")
aws_access_key=os.getenv("Access_key_ID")
aws_secret_key=os.getenv("Secret_access_key")
region=os.getenv("region")

journals=Blueprint("journals",__name__)
s3 = boto3.client('s3',aws_access_key_id=aws_access_key,aws_secret_access_key=aws_secret_key)

@journals.route(rule="/create-journals",methods=["GET","POST"])
def create_journals():
    if "user" in session:
        if request.method=='POST':
            uploaded_by=session["user"]
            timestamp_name=str(round(datetime.datetime.utcnow().timestamp()))
            upload_name=timestamp_name+"_"+uploaded_by
            form_data=request.files["bill_file"]
            # form_comment=request.form["comment"]
            data_to_insert={"user":uploaded_by,'document_name':upload_name,"upload_time":datetime.datetime.utcnow().timestamp(),"status":"Created"}
            s3.put_object(Body=form_data,Bucket=bucket_name,Key=f"Journals/{upload_name}")
            upload_journals.insert_one(data_to_insert)
            print("upload sucess")
            flash(message="CSV uploaded sucessfully",category='info')
            return redirect(url_for('receivable.create_csv_page'))
        else:
            return render_template("create-journal.html")
    else:
        return redirect(url_for('auth.login'))
    


@journals.route(rule="/read-journals")
def read_journals():
    if "user" in session:
        if session['role']=="Admin":
            mongo_data=upload_journals.find()
        else:
            mongo_data=upload_journals.find({'user':session['user']})
        print(mongo_data,"this is upload invoice")
        data=[]
        num=1
        for i in mongo_data:
            formated_time= datetime.datetime.utcfromtimestamp(i['upload_time']).strftime('%Y-%m-%d %H:%M:%S')
            i['upload_time']=formated_time
            i["id_num"]=num
            data.append(i)
            num=num+1
    return render_template("read-journal.html",data=data)

@journals.route(rule="/show-journals")
def show_journals():
    if "user" in session:
        doc_name = request.args.get('doc_name')
        obj = s3.get_object(Bucket=bucket_name, Key=f'Journals/{doc_name}')
        data_df = pd.read_csv(obj['Body'], sep=',')
        data=data_df.to_dict('records')
        columnNames = data_df.columns.values
        return render_template('show_journals_CSV.html',records=data,colnames=columnNames)
    else:
        return redirect(url_for('auth.login'))
