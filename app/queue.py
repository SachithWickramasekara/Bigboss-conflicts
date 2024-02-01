from flask import Blueprint,render_template,request,session,redirect,url_for
import boto3
import os
import datetime
from pymongo import MongoClient 


client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client[f"{os.getenv('db_name')}"]
mycollection = mydatabase['users']  
uploads=mydatabase["uploads"] 
queue=Blueprint("queue",__name__)

@queue.route(rule="/")
def my_queue():
    if 'user' in session :
        if session["role"]=="Admin":
            uploaded_data=uploads.find()
        elif session["role"]=="User":
            user=session["user"]
            uploaded_data=uploads.find({"user":user})
        data=[]
        # print(uploaded_data)
        for i in uploaded_data:
            # print(i,"this is i")
            formated_time= datetime.datetime.utcfromtimestamp(i['upload_time']).strftime('%Y-%m-%d %H:%M:%S')
            i['upload_time']=formated_time
            data.append(i)
        data.reverse()
        bills_data={"data":data}
        print(bills_data,"this is bill data for queue")
        return render_template("queue.html",data=bills_data)
    elif "user" not in session:
        return redirect(url_for('auth.login'))

@queue.route(rule="/add-data",methods=["POST"])
def add_data_from_queue():
    supplier_id=request.form["supplier"]
    company_data=request.form["company"]
    bill_number=request.form["bill_no"]
    currency=request.form["currency"]
    tax_type=request.form['tax_type']
    bill_date=request.form["bill_date"]
    due_date=request.form['due_date']
    print("supplier id",supplier_id)
    print("company",company_data)
    print("bill No",bill_number)
    print("Currency",currency)
    print("tax Type",tax_type)
    print("Bill Date",bill_date)
    print("Due Date",due_date)
    return {"data":""}
     