from typing import Union
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session  # Używaj Session, a nie SessionLocal
from pydantic import BaseModel
from passlib.context import CryptContext  # Do haszowania haseł
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Generator  # Import Generator dla typowania

# URL bazy danych SQLite
DATABASE_URL = "sqlite:///bikeway-db.db"

# Tworzenie silnika bazy danych (engine) oraz połączenie z bazą
engine = create_engine(DATABASE_URL)

# Podstawowa klasa dla SQLAlchemy, której będziemy używać do tworzenia tabel
Base = declarative_base()

# Tworzenie sesji połączenia z bazą danych
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Kontekst PassLib do haszowania haseł
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Inicjalizacja aplikacji FastAPI
app = FastAPI()

######## JWT KONFIGURACJA ########
SECRET_KEY = "5uOu4Q05M105"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

######## TABELA BAZY DANYCH ########
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

######## MODELE Pydantic ########
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

######## POMOCNICZE FUNKCJE ########
# Funkcja otwierająca połączenie z bazą danych
def get_db() -> Generator[Session, None, None]:  # Zwracamy obiekt Session
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

######## ENDPOINTY ########
# Endpoint do rejestracji użytkownika
@app.post("/register/")
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):  # Użyj Session
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User registered successfully"}

# Endpoint do logowania i uzyskiwania tokena JWT
@app.post("/login/", response_model=Token)
async def login(user_data: UserCreate, db: Session = Depends(get_db)):  # Użyj Session
    db_user = db.query(User).filter(User.email == user_data.email).first()
    
    if not db_user or not verify_password(user_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
