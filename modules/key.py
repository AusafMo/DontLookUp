import secrets
from pydantic import BaseModel
from .user import User
from .db import db

def insert_dlu_key(current_user: User):
    try:
        dlu_key = secrets.token_urlsafe(12)
        res =  db.keyMap.insert_one({"dlu_key": dlu_key, "gem_keys": [], "user": current_user.get("username")})
        if res.acknowledged == False:
            return {"message": "dlu_key not added"}
        return {"message": "dlu_key added", 'dlu_key': dlu_key}
    except Exception as e:
        return {"message": str(e)}
    
def get_dlu_keys(current_user: User):
    keys = db.keyMap.find({"user": current_user.get("username")})
    return {"keys": [key.get("dlu_key") for key in keys]}

def get_gem_keys(dlu_key: str):
    keys = db.keyMap.find_one({"dlu_key": dlu_key})
    return {"keys": keys.get("gem_keys")}

def insert_gem_key(dlu_key: str, new_key:str, current_user: User):
    try:
        res = db.keyMap.update_one({"dlu_key": dlu_key}, {"$push": {"gem_keys": new_key}})
        if res.matched_count == 0:
            return {"message": "dlu_key not found"}
    
        return {"message": "gem_key added"}
    except Exception as e:
        return {"message": str(e)}
