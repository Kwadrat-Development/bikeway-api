from typing import Union
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import Generator 
import math

DATABASE_URL = "sqlite:///bikeway-db.db"

engine = create_engine(DATABASE_URL)

Base = declarative_base()

app = FastAPI()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Route(Base):
    __tablename__ = 'routes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    discription = Column(String, nullable=False, unique=True)
    km = Column(String, nullable=False)


class Route_Local(Base):
    __tablename__ = 'route_localization'
    route_id = Column(Integer)
    x = Column(String, nullable=False)
    z = Column(String, nullable=False)

@app.post("/new_route_c/")
async def new_route_c(route_data: Route_Local, db: Session = Depends(get_db)):
    db.add(route_data[0])
    lenght = len(route_data)
    for i in range(lenght):
        if i == 0:
            continue
        if check_corner(route_data[i-1],route_data[i],route_data[i+1]):
            db.add(route_data[i])
        
@app.post("/new_route/")
async def new_route(route: Route, db:Session = Depends(get_db)):
    db.add(route)

def distance(stx,sty,ndx,ndy):
    return math.sqrt((stx-ndx)*(stx-ndx)+(sty-ndy)*(sty-ndy))

def check_corner(st,corner,rd):
    r=False
    a = distance(st,corner)
    b = distance(corner,rd)
    c = distance(st,rd)

    if math.degrees(math.cos((c**-a**-b*b)/-2*a*b)) > 30:
        r=True
    return r