from pydantic import BaseModel
from typing import Dict, Optional

class ScrapingRequest(BaseModel):
    url: str
    selectors: Dict[str, str]
    wait_time: Optional[int] = 10
    headless: Optional[bool] = True

class LoginScrapingRequest(ScrapingRequest):
    username: str
    password: str

class AribaLoginRequest(BaseModel):
    email: str
    password: str
    headless: Optional[bool] = False
    download_path: Optional[str] = None 