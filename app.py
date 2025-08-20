from flask import Flask
from applications.database import db

app = None

def create_app():
    app=Flask(__name__)
    app.debug= True
    app.config["SECRET_KEY"] = "Ds_PghD9XbCg8LLzfAwFG5kkXlAlHvwTyBdUDtKXPfA" 
    app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///parking_app.sqlite3" 
    db.init_app(app) 
    app.app_context().push() 

    from applications.models import User, Parkinglot, Parkingspot, Reservepkspot
    db.create_all()
    
    return app

app=create_app()

from applications.controllers import *

if __name__=='__main__':
    app.run() 

    