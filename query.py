from fastapi import HTTPException, Depends, Security
import google.generativeai as genai
from pymongo.mongo_client import MongoClient
from auth import checkDluKey, get_current_user
from user import User
import os
from pydantic import BaseModel
from db import db

def query(keyword:str =None, temperature: float = .5, dlu_key: str = Security(checkDluKey), current_user: User = Depends(get_current_user)):
    keyword = keyword.replace("%20", " ")

    gem_keys = db.keyMap.find_one({"dlu_key": dlu_key}).get("gem_keys")[0]
    
    genai.configure(api_key = gem_keys)

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
