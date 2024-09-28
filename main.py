from typing import Union
from fastapi import FastAPI
import sqlalchemy
import sqlite3
from sqlalchemy import create_engine,declarative_base, Column, Integer, String, sessionmaker
from pydantic import BaseModel

app = FastAPI()
engine = create_engine('sqlite:///bikeway-db.db')
Base = declarative_base()
 
######## DATABASE
class Bikeway(Base):
######## USER TABLE CREATE
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True,autoincrement=True) 
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)

######## CLASS USER FOR IMPORT
class UserCreate(BaseModel):
    id: int
    username: str
    email: str
    passw: str

@app.post("/register/")
async def create_user(user_data: UserCreate):
    username = user_data.username
    email = user_data.email
    passw = user_data.passw 
    return {
        "msg":"udalo sie zarejestrowac:"+username+" "+email+" "+passw
    }

@app.post("/login/")
async def create_user(user_data: UserCreate):
    email = user_data.email
    passw = user_data.passw 
    return {
        "msg":"udalo sie zalogowac:"+" "+email+" "+passw
    }

if __name__ == "__main__":
    import uvicorn
 
    uvicorn.run(app, host="127.0.0.1", port=8000)
