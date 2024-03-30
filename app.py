import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

def initcon():
    uri = os.getenv("murl")
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.get_database("dlu")
    return db
db = initcon()

api_key_header = APIKeyHeader(name="api_key")
def checkDluKey(api_key_header: str = Security(api_key_header)) -> str:
    if db.keyMap.find_one({"dlu_key": api_key_header}) is not None:
        return api_key_header
    
    raise HTTPException(
        status_code= status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing DLU API Key",
    )

@app.post("/createDluKey/{new_key}")
async def insert(new_key:str):
    try:
       res =  db.keyMap.insert_one({"dlu_key": new_key, "gem_keys": []})
       if res.acknowledged == False:
            return {"message": "api key not added"}
       return {"message": "api key added"}
    except Exception as e:
        return {"message": str(e)}

@app.post("/protected/createGemKey/{dlu_key}/{new_key}")
async def insert(dlu_key: str, new_key:str):
    try:
        res = db.keyMap.update_one({"dlu_key": dlu_key}, {"$push": {"gem_keys": new_key}})
        if res.matched_count == 0:
            return {"message": "dlu_key not found"}
    
        return {"message": "api key added"}
    except Exception as e:
        return {"message": str(e)}

@app.get("/protected/{keyword}")
async def query(keyword:str =None, temperature: float = .5, dlu_key: str = Security(checkDluKey) ):

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