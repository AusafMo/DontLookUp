from fastapi import HTTPException, Security, Depends, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
import jwt
from pymongo.mongo_client import MongoClient
import os
from db import db
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

def get_current_user(token: str = Security(OAuth2PasswordBearer(tokenUrl="login"))):
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

def checkDluKey(api_key_header: str = Security(APIKeyHeader(name="api_key"))):
    if db.keyMap.find_one({"dlu_key": api_key_header}) is not None:
        return api_key_header
    
    raise HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing DLU API Key",
    )
