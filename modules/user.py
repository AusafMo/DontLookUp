from fastapi import HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext
import datetime
from datetime import timedelta
import jwt
from .db import db
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    email: str
    hashed_password: str

def register(user: User):
    user.hashed_password = pwd_context.hash(user.hashed_password)
    exist = db.users.find_one({"username": user.username, "email": user.email})
    
    if exist is not None:
        return {"message": "user already exists"}
    
    res = db.users.insert_one({"username": user.username, "email": user.email, "hashed_password": user.hashed_password})
    if res.acknowledged == False:
        return {"message": "user not added"}
    return {'message': "user registration success"}

def create_access_token(data: dict, expires_delta: timedelta, SECRET_KEY, ALGORITHM):
    expire = datetime.datetime.now(datetime.UTC) + expires_delta
    data['exp'] = expire
    return jwt.encode(payload=data, key=SECRET_KEY, algorithm=ALGORITHM)

def login(username: str, password: str):
    user = db.users.find_one({"username": username})
    if user is None:
        return {"message": "user not found"}
    
    if pwd_context.verify(password, user.get("hashed_password")):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires, SECRET_KEY=SECRET_KEY, ALGORITHM=ALGORITHM
        )
        return {"access_token": access_token, "token_type": "bearer"}
    return {"message": "incorrect password"}
