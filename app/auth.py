from flask import Blueprint,render_template,request,flash,redirect,url_for,session,redirect
from .models import User
import os
import datetime
from pymongo import MongoClient 
from flask_bcrypt import Bcrypt
client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client[f"{os.getenv('db_name')}"]
mycollection = mydatabase['users']  
uploads=mydatabase["uploads"]
auth=Blueprint("auth",__name__)
bcrypt = Bcrypt()




@auth.route(rule="/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        print("post method working")
        if request.form:
            print("got form")
            email=request.form["email"]
            password=request.form["password"]
            print("got data from new template")
            if email and password:
                user_data=User().login_user(email=email,password=password)
                if user_data and user_data["error"]==False:
                    flash(message="login successfull...",category="success")
                    print("VIEW REDIRECTION")
                    if "access_token" not in session:
                            return redirect(url_for('x_auth.get_access_tokens_api'))
                    if "company" not in session:
                        return redirect(url_for('x_auth.get_tenant'))
                    try:
                        if "access_token" not in session:
                            return redirect(url_for('x_auth.get_access_tokens_api'))
                    
                    except :
                        return redirect(url_for('x_auth.get_tenant'))
                    
                    return redirect(url_for("views.dashboard"))
                else:
                    flash(message="Incorrect password ... please try again...",category="error")
            else:
                flash(message="user data not found",category="error")
    print("get method working")
    return render_template("sign-in.html")

@auth.route(rule="/logout")
def logout():

    User().logout_user()
    print("logout sucessfull")
    return redirect(url_for("auth.login"))

@auth.route(rule="/sign-up",methods=["GET","POST"])
def sign_in():
    if request.method=="POST" and session["user"]:
        print("signing up ")
        if request.form:
            print(request.form)
            user_name=request.form["username"]
            email=request.form["email"]
            password_1=request.form["password1"]
            password_2=request.form["password2"]
            role=request.form["role"]
            if role=="--Role--":
                return redirect(url_for('auth.sign_in'))
            print(password_1,"this is password")
            if password_1 == password_2:
                check_mail=mycollection.find_one({"email":email})
                if check_mail==None:
                    user_sign_data={"user":user_name,"password":password_1,"created_at":datetime.datetime.utcnow(),"email":email,"role":role}
                    print(user_sign_data)
                    User.sign_up_user(user_sign_data)
                    session["user"]=user_name
                    return redirect(url_for('x_auth.get_first_auth_token'))
    
    return render_template("sign-up.html")
                
@auth.route(rule="/view-profile")
def view_profile():
    data=mycollection.find_one({"user":session["user"]})
    # print(data)
    user_name=data["user"]
    email=data["email"]
    role=data['role']
    tenant=[]
    for i in data["tenant_list"]:
        # print(i["tenantName"])
        tenant.append(i["tenantName"])
        # for j in i:
        #     print(j["tenantName"])
    
    return render_template("auth/profile.html",user_name=user_name,email=email,role=role,tenants=tenant)

@auth.route(rule="/delete-user",methods=["GET","POST"])
def delete_users():

    if request.method=='POST':
        delete_name=request.form["delete_user"]
        try:
            mycollection.delete_one({'user':delete_name})
            print("delete successful")
            return redirect(url_for('auth.delete_users'))
        except:
            print("")
            return {"data":"could not found the user"}
        
    data=mycollection.find()
    user_list=[]
    for i in data:
        print(i["user"])
        user_list.append(i["user"])
    return render_template('auth/delete_user.html',user_list=user_list)

@auth.route(rule="/in-progress")
def inprogress_page():
    return render_template("in-progress.html")


# Fix routing below

@auth.route(rule="/notifications")
def notifications():
    return render_template("notifications.html")


@auth.route(rule="/other-notifications")
def notificationsO():
    return render_template("notifications-2.html")


@auth.route(rule="/accounts-payable")
def accountsPayable():
    return render_template("accounts-payable.html")

@auth.route(rule="/accounts-payable/view-bill")
def accountsPayableViewBill():
    return render_template("ap-view-bill.html")

@auth.route(rule="/accounts-recievable")
def accountsRecievable():
    return render_template("accounts-recievable.html")

@auth.route(rule="/accounts-recievable/view-bill")
def accountsRecievableViewBill():
    return render_template("ar-view-bill.html")

@auth.route(rule="/email/password-reset")
def emailPwReset():
    return render_template("email-pw-reset.html")