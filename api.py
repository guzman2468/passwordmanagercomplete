from PyQt6.QtWidgets import *
from pydantic import BaseModel
from pymongo import MongoClient
import config
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import config

app = FastAPI()
client = MongoClient(config.uri)
db = client["password_manager"]
collection = db["details"]

class Website(BaseModel):
    site_name: str
    site_username: str
    site_password: str


class User(BaseModel):
    username: str
    password: str
    websites: Optional[List[Website]] = None

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
        return {"initial_username" : user.username , "initial_password" : user.password}
    else:
        raise HTTPException(status_code=400, detail="No account matching those credentials found."
                                                    " Verify all info is correctly inputted")
    #TODO: refactor message below
    return {"message" : "reached end of login endpoint"}


@app.get("/api/searchSites")
def searchSites(user: User):
    '''
    This endpoint is called only after the user successfully logs in
    ensuring that data is protected and searching sites cannot occur before this
    :param user: User JSON object that has the username, password (both required), and site_name (optional)
    :return: JSON object showing the name, username, and password for the website given
    '''
    existing_user = collection.find_one({"initial_username": user.username, "initial_password": user.password},
                                        {"websites": 1})
    if not existing_user:
        raise HTTPException(status_code=400, detail="No user found with those credentials")
    if "websites" not in existing_user:
        raise HTTPException(status_code=400, detail="No websites found for user. Please add website.")

    for website in existing_user["websites"]:
        if user.websites[0].site_name == None:
            return {"message" : "site_name is missing"}
        if website["name"].lower() == user.websites[0].site_name.lower():
            return {
                "website_name" : website["name"],
                "website_username" : website["username"],
                "website_password" : website["password"]
            }
    raise HTTPException(status_code=404, detail="Given site not found for this user.")
    return {"message" : "reached end of searchSites"}


@app.post("/api/addSite")
def addSite(user: User):
    existing_user = collection.find_one({"initial_username": user.username, "initial_password": user.password},
                                        {"websites": 1})
    if not existing_user:
        raise HTTPException(status_code=400, detail="No user found with those credentials")

    if not user.websites or user.websites[0].site_name is None:
        raise HTTPException(status_code=400, detail="websites.site_name is missing")

    for website in existing_user["websites"]:
        if website["name"] == user.websites[0].site_name:
            raise HTTPException(status_code=400, detail="Website already entered. Please choose a new site to add.")

        new_site = {
            "name": user.websites[0].site_name,
            "username": user.websites[0].site_username,
            "password": user.websites[0].site_password
        }

        collection.update_one({"initial_username" : user.username, "initial_password" : user.password},
                              {"$push" : {"websites": new_site}})

        return {"message": "Website added successfully"}

