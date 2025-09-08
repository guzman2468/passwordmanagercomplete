from PyQt6.QtWidgets import *
from pydantic import BaseModel
from pymongo import MongoClient
import config
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import config

app = FastAPI()
client = MongoClient(config.uri)
db = client["password_manager"]
collection = db["details"]

class User(BaseModel):
    username: str
    password: str

@app.get("/")
def root():
    return {"Hello" : "World"}
@app.post("/api/accountCreate")
def accountCreate(user: User):
    if user.username.strip() == "" or user.password.strip == "":
        raise HTTPException(status_code=400, detail="All fields must be filled")
    if len(user.username) < 4 or len(user.password) < 4:
        raise HTTPException(status_code=400, detail="Username and password must be at least 4 characters long")

    existing_user = collection.find_one({"initial_username" : user.username})

    if existing_user:
        raise HTTPException(status_code=400, detail="Username is already taken")

    document = {"initial_username" : user.username, "initial_password" : user.password}
    collection.insert_one(document)
    return {"message" : "Account created successfully"}

@app.post("/api/login")
def login(user: User):
    if user.username.strip() == "" or user.password.strip == "":
        raise HTTPException(status_code=400, detail="All fields must be filled")

    existing_user = collection.find_one({"initial_username": user.username, "initial_password" : user.password})

    if existing_user:
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=400, detail="No account matching those credentials found."
                                                    " Verify all info is correctly inputted")
    #TODO: refactor message below
    return {"message" : "reached end of login endpoint"}


# @app.get("/api/users/{username}/")