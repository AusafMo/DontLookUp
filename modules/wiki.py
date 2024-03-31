from fastapi import HTTPException, Depends, Security
from .auth import checkDluKey
from .user import User
from .db import session
from pydantic import BaseModel

s = session()
def wikiSummary(keyword:str =None, dlu_key: str = Security(checkDluKey)):
    keyword = keyword.replace("%20", " ")
    try:
        search = s.get(f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={keyword}&format=json")
        if search.status_code != 200:
            return {"error": "Couldnt query Wikipedia API"}
        search = search.json()
        if search.get('query').get('search'):
            title = search.get('query').get('search')[0].get('title')
            res = s.get(f'https://en.m.wikipedia.org/api/rest_v1/page/summary/{title}')
            res = res.json()
            return {"keyword": keyword, "extract": res.get('extract')}
    except Exception as e:
        return {"keyword": keyword, "error": str(e)}   
    finally:
        s.close()