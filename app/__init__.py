from flask import Flask
from pymongo import MongoClient 
import os
import datetime
import json

client = MongoClient(os.getenv("mongo_connetion_string"))
mydatabase = client[f"{os.getenv('db_name')}"]
mycollection = mydatabase['users']  
uploads=mydatabase["uploads"]
tax_table=mydatabase["tax_type"]


def create_app():
    app=Flask(__name__)
    app.config["SECRET_KEY"]=f'{os.getenv("flask_secret_key")}'
    from .auth import auth
    from .views import views
    from .xero_api_auth import x_auth
    from .bills import bills
    from .user_control import user_control
    from .queue import queue
    from .receivable import receivable
    from .journals import journals

    app.register_blueprint(queue,url_prefix="/queue")
    app.register_blueprint(views,url_prefix="/")
    app.register_blueprint(auth,url_prefix="/auth")
    app.register_blueprint(x_auth,url_prefix="/x-auth")
    app.register_blueprint(bills,url_prefix="/bills")
    app.register_blueprint(user_control,url_prefix="/user-control")
    app.register_blueprint(receivable,url_prefix="/receivable")
    app.register_blueprint(journals,url_prefix="/journals")
    
    if tax_table.count_documents({}) == 0:
    # Read JSON file
        with open('tax_type.json', 'r') as file:
            data = json.load(file)

        # Insert data into the collection
        tax_table.insert_many(data)
        print('Data inserted successfully.')

    else:
        print('Data already exists in the collection.')
    db_collection_list=mydatabase.list_collection_names()
    if "users" in db_collection_list:
        print("db already exists")
    else:
        print("add user json")
        data={
            "user":"Admin",
            'password':'$2b$12$BrEnRQBJCnfKJI5P6MTDLe2dKBvWQ9CG97DfNm5GvCmoM.8qchuqm',
            'email':"admin@bpo.com",
            'role':"Admin",
            'created_at':datetime.datetime.utcnow()
        }
        try:
            mycollection.insert_one(data)
            print("added admin user")
        except:
            print("mongo updatation failed")
        
    return app
