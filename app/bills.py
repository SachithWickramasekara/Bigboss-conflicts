#/create-bill
from flask import Blueprint,render_template,request,flash,redirect,url_for,session,flash
from .models import User
import datetime
import boto3
import os
import json
import base64
import jinja2
import PyPDF2
from pdf2image import convert_from_bytes
from io import BytesIO
from pymongo import MongoClient 
from .utils import get_supplier_list
import botocore
from pdf2image import convert_from_path
import pandas as pd

client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client[f"{os.getenv('db_name')}"]
mycollection = mydatabase['users']  
uploads=mydatabase["uploads"]
tax_type=mydatabase["tax_type"]
line_item_data=mydatabase["line_item_data"]


bucket_name=os.getenv("bucket_name")
aws_access_key=os.getenv("Access_key_ID")
aws_secret_key=os.getenv("Secret_access_key")
region=os.getenv("region")


bills=Blueprint("bills",__name__)
s3 = boto3.client('s3',aws_access_key_id=aws_access_key,aws_secret_access_key=aws_secret_key)

# Set the allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else None

def get_file_name(filename):
    return filename.rsplit('.', 1)[0] if '.' in filename else filename

def split_pdf_and_upload_to_s3(file, bucket_name, key):
        images = convert_from_bytes(file, fmt='png')
        try:
            for page_number, image in enumerate(images):
                # Convert image to bytes
                newkey = key+"_"+str(page_number)
                img_bytes = BytesIO()
                image.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                s3.put_object(Body=img_bytes,Bucket=bucket_name,Key=newkey)
                print(f"Uploaded page {page_number + 1} to S3: {key}")
        except Exception as e:
            print("Exception occured",e)

    

def get_files_from_react(data):
    try:
        try:
            
            photo_data=data["image"].split(",")[1]
            photo_data=base64.b64decode(photo_data)
            print("tried complete")
        except:
            
            photo_data=data["image"]
            photo_data=base64.b64decode(photo_data)
            print("exception complete")
        print("got tracker ids too..")
        uploaded_by=data['user']
        comment=data['comment']
        company=data['company']
        supplier=data['supplier']
        if  photo_data :# and found_face:
            print("passed everything")
            return photo_data,uploaded_by,comment,company,supplier
        else:
            return False
    except KeyError:
        return "datas are missing"

def check_pdf_format(pdf_file):
    final_df = pd.DataFrame(columns = ['Keys','Values'])
    images = convert_from_path(pdf_file)

@bills.route("/Upload-Bill",methods=["POST"])
def uploads_from_mobiles():
    try:
        api_data=request.get_json()
        try:
            timestamp_name=str(round(datetime.datetime.utcnow().timestamp()))
            print("entered here")
            #return photo_data,uploaded_by,comment,company,supplier
            photo_data,uploaded_by,comment,company,supplier=get_files_from_react(api_data)
            print("got 4 datas")
            if photo_data:
                upload_name=timestamp_name+"_"+ uploaded_by
                # photo_send=send_to_s3(photo_data,bucket_name)
                if  photo_data and company and supplier:
                    data={"user":uploaded_by,"company":company,"supplier":supplier,"document_name":upload_name,"comment":comment,"status":"Created","upload_time":datetime.datetime.utcnow().timestamp()}
                    try:
                        # status_pending(result,data)
                        s3.put_object(Body=photo_data,Bucket=bucket_name,Key=f"Mobile-Uploads/{upload_name}/{upload_name}")
                        uploads.insert_one(data)
                    except:
                        print("failed here")
                    return {"message":"Data successfully uploaded.","error":False},200
                
                else :
                    return {"message":"No data was found.","error":True},401
                
            else:
                return {"message":"cannot found face from id card.","error":True},402
        except:
            print(dict(api_data).keys())
            return {"message":"Image is blurred. Try again.","error":True},403
    except:
        return {"message":"No data received.","error":True},404
    



@bills.route(rule="/create-bill",methods=["GET","POST"])
def create_bill_page():
    if "user" in session:
        if request.method=='POST':
            #name for s3 file
            uploaded_by=session["user"]
            timestamp_name=str(round(datetime.datetime.utcnow().timestamp()))
            upload_name=timestamp_name+"_"+uploaded_by
            form_data=request.files.getlist("file[]")
            print(form_data)
            company_name=request.form["company"]
            supplier=request.form["supplier"]
            form_comment=request.form["comment"]
            doc_type=request.form["doc_type"]
            account_type=request.form['acc_type']
            # print(len(form_data))
            print("about to upload")
            for file in form_data:
                if file and allowed_file(file.filename):
                    print(file)
                    if get_file_extension(file.filename)=="pdf":
                        split_pdf_and_upload_to_s3(file.read(), bucket_name, f"bills-processing/{upload_name}/{get_file_name(file.filename)}")
                    else:
                        s3.put_object(Body=file,Bucket=bucket_name,Key=f"bills-processing/{upload_name}/{file.filename}")
                else:
                    flash(message="Invalid File Format",category='danger')
                    return redirect(url_for('bills.create_bill_page'))
            data_to_insert={"account_type":account_type,"document_type":doc_type,"supplier":supplier,"user":uploaded_by,'document_name':upload_name,"upload_time":datetime.datetime.utcnow().timestamp(),"comment":form_comment,"status":"Created","upload_company":company_name}
            # s3.put_object(Body=form_data,Bucket=bucket_name,Key=f"bills/{upload_name}/{upload_name}")
            uploads.insert_one(data_to_insert)
            print("upload success")
            flash(message="File uploaded sucessfully",category='info')
            return redirect(url_for('bills.create_bill_page'))
        else:
            # company_name_list=mycollection.find_one({"user":session["user"]})
            if "company" not in session:
                return redirect(url_for('x_auth.get_tenant'))
            # print(session["user"],session["company"])
            if "user" in session and "company" in session:
                supplier=get_supplier_list(session["user"],session["company"])
            elif "company" not in session:
                return redirect(url_for('x_auth.get_tenant'))
            try:
                return render_template("create-bill.html",supplier=supplier)
            except TypeError:
                return redirect(url_for("manage-user.manage_user"))
    else:
        return redirect(url_for('auth.login'))

@bills.route(rule="/view-bill")
def view_bills():
        if 'user' in session :
            if session["role"]=="Admin":
                uploaded_data=uploads.find()
            elif session["role"]=="User":
                user=session["user"]
                uploaded_data=uploads.find({"user":user})
            data=[]
            num=1
            for i in uploaded_data:
                formated_time= datetime.datetime.utcfromtimestamp(i['upload_time']).strftime('%Y-%m-%d %H:%M:%S')
                i['upload_time']=formated_time
                i["id_num"]=num
                data.append(i)
                num=num+1
            bills_data={"data":data}
            return render_template("view-bill.html",data=bills_data)
        elif "user" not in session:
            return redirect(url_for('auth.login'))
        
@bills.route(rule="/edit-bill")
def edit_bill():
    if "user" in session:
        doc_name = request.args.get('doc_name')
        print(doc_name)
        response = s3.list_objects(Bucket=bucket_name, Prefix=f'PROCESSED/{doc_name}')
        files=[]
        # print(response)
        try:
            mongo_line_data=uploads.find_one({'document_name':doc_name})
            print(mongo_line_data)
            if 'line_item'in  mongo_line_data:
                line_item=mongo_line_data['line_item']
                try:
                    line_item=json.loads(line_item)
                except TypeError:
                    pass

                print("yes there is line data here")
                for i in response["Contents"]:
                    name=i["Key"]
                    print(name)
                    data=s3.get_object(Bucket=bucket_name,Key=name)
                    image_data_byte=data["Body"].read()
                    data=base64.b64encode(image_data_byte).decode("utf-8")
                    files.append(data)
                # print(files)
                    tax_type_list=[]
                    tax_type_table=tax_type.find()
                    for i in tax_type_table:
                        tax_type_list.append(i)
                    if "company" in session:
                        supplier=get_supplier_list(user=session["user"],current_company=session["company"])
                    else:
                        return redirect(url_for('manage-user.manage_user'))
                    mongo_data=mycollection.find_one({'user':session['user']})
                    currency_data=mongo_data.get('currencies')

                    if currency_data!=None:
                        currency=currency_data
                    else:
                        return redirect(url_for("x_auth.get_currency"))
                    # mongo data send description
                # print(type(line_item))
                # try:
                return render_template("edit-invoice.html",currency=currency,img_list=files,tax_type_list=tax_type_list,supplier=supplier,doc_name=doc_name,line_data=mongo_line_data,line_item=line_item)
                # except:
                #     return render_template("edit-invoice-list.html",currency=currency,img_list=files,tax_type_list=tax_type_list,doc_name=doc_name,line_item=line_item)
            else:
                print("thre is no line data")
                for i in response["Contents"]:
                    name=i["Key"]
                    print(name)
                    data=s3.get_object(Bucket=bucket_name,Key=name)
                    image_data_byte=data["Body"].read()
                    data=base64.b64encode(image_data_byte).decode("utf-8")
                    files.append(data)
                # print(files)
                    tax_type_list=[]
                    tax_type_table=tax_type.find()
                    for i in tax_type_table:
                        tax_type_list.append(i)
                    if "company" in session:
                        supplier=get_supplier_list(user=session["user"],current_company=session["company"])
                    else:
                        return redirect(url_for('manage-user.manage_user'))
                    mongo_data=mycollection.find_one({'user':session['user']})
                    currency_data=mongo_data.get('currencies')
                    if currency_data!=None:
                        currency=currency_data
                    else:
                        return redirect(url_for("x_auth.get_currency"))
                return render_template("edit-invoice.html",currency=currency,img_list=files,tax_type_list=tax_type_list,supplier=supplier,doc_name=doc_name)
        except KeyError as e:
            print(e)
            return redirect(url_for('views.dashboard'))

@bills.route(rule="/change-state/<doc_name>/<status>")
def change_status(doc_name,status):
    uploads.update_one({"document_name":doc_name},{"$set":{"status":status}})
    data=uploads.find_one({"document_name":doc_name})
    return str(data)
     
@bills.route(rule='/add-record',methods=["POST"])
def add_record():
    if 'user' in session:
        final_dict={}
        # print(request.form,"return valu")
        doc_name=request.form['doc_name']
        company=request.form['company']
        supplier=request.form["supplier"]
        invoice_num=request.form["bill_num"]
        currency=request.form["currency"]
        tax_type_over_all=request.form["tax_type_over_all"]
        bill_date=request.form["bill_date"]
        due_date=request.form["due_date"]
        final_dict["company"]=company
        final_dict["supplier"]=supplier
        final_dict["invoice_num"]=invoice_num
        final_dict["currency"]=currency
        final_dict["tax_type_over_all"]=tax_type_over_all
        final_dict["bill_date"]=bill_date
        final_dict["due_date"]=due_date
        final_dict['doc_name']=doc_name
        print(request.form.to_dict(flat=False),"this is accutal data")
        description=request.form.getlist('description')
        account=request.form.getlist('account')
        quantity=request.form.getlist('quantity')
        unit_price=request.form.getlist('unit_price')
        tax_type=request.form.getlist('tax_type')
        total_amount=request.form.getlist('total_amount')
        over_all_list=[]
        for i in range(len(description)):
            # print(i,"i is printing")
            data_row={}
            data_row['description']=description[i]
            data_row['account']=account[i]
            data_row['quantity']=quantity[i]
            data_row['unit_price']=unit_price[i]
            data_row['tax_type']=tax_type[i]
            data_row['total_amount']=total_amount[i]
            over_all_list.append(data_row)
        final_dict["line_item"]=over_all_list
        final_dict['uploaded_by']=session['user']
        final_dict['status']="In-progress"
        # print(final_dict,"this is data")
        uploads.update_one({"document_name":doc_name},{'$set':final_dict})
        return redirect(url_for('queue.my_queue'))

@bills.route(rule="/make-pending",methods=["POST"])
def make_pending():
    if "user" in session:
        final_dict={}
        # print(request.form,"return valu")
        doc_name=request.form['doc_name']
        # company=request.form['company']
        # supplier=request.form["supplier"]
        # invoice_num=request.form["bill_num"]
        # currency=request.form["currency"]
        # tax_type_over_all=request.form["tax_type_over_all"]
        # bill_date=request.form["bill_date"]
        # due_date=request.form["due_date"]
        # final_dict["company"]=company
        # final_dict["supplier"]=supplier
        # final_dict["invoice_num"]=invoice_num
        # final_dict["currency"]=currency
        # final_dict["tax_type_over_all"]=tax_type_over_all
        # final_dict["bill_date"]=bill_date
        # final_dict["due_date"]=due_date
        # final_dict['doc_name']=doc_name
        # print(request.form.to_dict(flat=False),"this is accutal data")
        # description=request.form.getlist('description')
        # account=request.form.getlist('account')
        # quantity=request.form.getlist('quantity')
        # unit_price=request.form.getlist('unit_price')
        # tax_type=request.form.getlist('tax_type')
        # total_amount=request.form.getlist('total_amount')
        # over_all_list=[]
        # for i in range(len(description)):
        #     # print(i,"i is printing")
        #     data_row={}
        #     data_row['description']=description[i]
        #     data_row['account']=account[i]
        #     data_row['quantity']=quantity[i]
        #     data_row['unit_price']=unit_price[i]
        #     data_row['tax_type']=tax_type[i]
        #     data_row['total_amount']=total_amount[i]
        #     over_all_list.append(data_row)
        # final_dict["line_item"]=over_all_list
        # final_dict['uploaded_by']=session['user']
        # final_dict['status']="Pending"
        # print(final_dict,"this is data")
        uploads.update_one({"document_name":doc_name},{'$set':{'status':"Pending"}})
        return redirect(url_for('queue.my_queue'))

    else:
        return redirect(url_for('auth.login'))
    
@bills.route(rule="/document_queue")
def document_queue():
    return render_template("document-queue.html")

@bills.route(rule="/view-document")
def view_document():
    return render_template("view-document.html")

