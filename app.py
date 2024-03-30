import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel
from passlib.context import CryptContext
import datetime
from datetime import timedelta
import jwt

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()

def initcon():
    uri = os.getenv("murl")
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.get_database("dlu")
    return db
db = initcon()

SECRET_KEY = os.getenv("secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class User(BaseModel):
    username: str
    email: str
    hashed_password: str

@app.post("/register")
async def register(user: User):
    user.hashed_password = pwd_context.hash(user.hashed_password)
    exist = db.users.find_one({"username": user.username, "email": user.email})
    
    if exist is not None:
        return {"message": "user already exists"}
    
    res = db.users.insert_one({"username": user.username, "email": user.email, "hashed_password": user.hashed_password})
    if res.acknowledged == False:
        return {"message": "user not added"}
    return {'message': "user registration success"}


def create_access_token(data: dict, expires_delta: timedelta):
    expire = datetime.datetime.now(datetime.UTC) + expires_delta
    data['exp'] = expire
    return jwt.encode(payload=data, key=SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Security(OAuth2PasswordBearer(tokenUrl="login"))):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception as e:
        raise credentials_exception
    user = db.users.find_one({"username": username})
    return user


@app.post("/login")
async def login(username: str, password: str):
    user = db.users.find_one({"username": username})
    if user is None:
        return {"message": "user not found"}
    
    if pwd_context.verify(password, user.get("hashed_password")):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    return {"message": "incorrect password"}


api_key_header = APIKeyHeader(name="api_key")
def checkDluKey(api_key_header: str = Security(api_key_header)) -> str:
    if db.keyMap.find_one({"dlu_key": api_key_header}) is not None:
        return api_key_header
    
    raise HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing DLU API Key",
    )

@app.post("/protected/createDluKey/{new_key}")
async def insert_dlu_key(new_key:str,  current_user: User = Depends(get_current_user)):
    try:
       res =  db.keyMap.insert_one({"dlu_key": new_key, "gem_keys": [], "user": current_user.get("username")})
       if res.acknowledged == False:
            return {"message": "dlu_key not added"}
       return {"message": "dlu_key added"}
    except Exception as e:
        return {"message": str(e)}

@app.post("/protected/createGemKey/{dlu_key}/{new_key}")
async def insert_gem_key(dlu_key: str, new_key:str,  current_user: User = Depends(get_current_user)):
    try:
        res = db.keyMap.update_one({"dlu_key": dlu_key}, {"$push": {"gem_keys": new_key}})
        if res.matched_count == 0:
            return {"message": "dlu_key not found"}
    
        return {"message": "gem_key added"}
    except Exception as e:
        return {"message": str(e)}

@app.get("/protected/{keyword}")
async def query(keyword:str =None, temperature: float = .5, dlu_key: str = Security(checkDluKey), current_user: User = Depends(get_current_user) ):

    keyword = keyword.replace("%20", " ")

    gem_keys = db.keyMap.find_one({"dlu_key": dlu_key}).get("gem_keys")[0]
    
    resp = genai.configure(api_key = gem_keys)

    model = genai.GenerativeModel('gemini-pro')

    prompt =  f"""tell me about {keyword} in no more than 50 words""",    
    generation_config = {
        "max_output_tokens": 1024,
        "temperature": 0.5,
        "top_p": 1,
    }
    try:
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )
        return {"prompt": prompt, "response": response.text}
    except Exception as e:
        return {"prompt": prompt, "error": str(e)}   
