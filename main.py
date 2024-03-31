from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from user import User, register, login
from auth import get_current_user, checkDluKey
from key import insert_dlu_key, get_dlu_keys, get_gem_keys, insert_gem_key
from query import query

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
api_key_header = APIKeyHeader(name="api_key")


@app.post("/register")
async def register_user(user: User):
    return register(user)

@app.post("/login")
async def user_login(username: str, password: str):
    return login(username, password)

@app.post("/protected/createDluKey/")
async def create_dlu_key(current_user: User = Depends(get_current_user)):
    return insert_dlu_key(current_user)

@app.get("/protected/getDluKeys")
async def get_dlu_keys_route(current_user: User = Depends(get_current_user)):
    return get_dlu_keys(current_user)

@app.get("/protected/getGemKeys/{dlu_key}")
async def get_gem_keys_route(dlu_key: str, current_user: User = Depends(get_current_user)):
    return get_gem_keys(dlu_key)

@app.post("/protected/createGemKey/{dlu_key}/{new_key}")
async def create_gem_key(dlu_key: str, new_key:str, current_user: User = Depends(get_current_user)):
    return insert_gem_key(dlu_key, new_key, current_user)

@app.get("/protected/{keyword}")
async def search_query(keyword: str = None, temperature: float = .5, dlu_key: str = Depends(checkDluKey), current_user: User = Depends(get_current_user)):
    return query(keyword, temperature, dlu_key, current_user)
