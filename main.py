from typing import Union
from fastapi import FastAPI, Depends, HTTPException, status
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from passlib.context import CryptContext  # Do haszowania haseł
from jose import JWTError, jwt  # Do generowania i weryfikacji tokenów JWT
from datetime import datetime, timedelta

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
# Sekret klucz do podpisywania tokenów (powinien być mocniejszy i trzymany bezpiecznie)
SECRET_KEY = "5uOu4Q05M105"
# Algorytm szyfrowania używany do podpisywania tokenów JWT
ALGORITHM = "HS256"
# Czas wygaśnięcia tokena (w minutach)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

######## TABELA BAZY DANYCH ########
# Model SQLAlchemy dla tabeli 'users' w bazie danych
class User(Base):
    # Nazwa tabeli
    __tablename__ = 'users'

    # Kolumny tabeli (id, name, email, hashed_password)
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)

# Tworzenie tabeli w bazie danych (jeśli nie istnieje)
Base.metadata.create_all(bind=engine)

######## MODELE Pydantic ########
# Model Pydantic do rejestracji nowego użytkownika
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

# Model Pydantic do odpowiedzi zwracającej token JWT
class Token(BaseModel):
    access_token: str
    token_type: str

######## POMOCNICZE FUNKCJE ########
# Funkcja, która otwiera połączenie z bazą danych
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Funkcja do haszowania haseł
def get_password_hash(password: str):
    return pwd_context.hash(password)

# Funkcja do weryfikacji hasła wprowadzonego przez użytkownika z hasłem w bazie
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Funkcja do generowania tokenu JWT
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()  # Tworzenie kopii danych użytkownika
    if expires_delta:
        expire = datetime.now() + expires_delta  # Dodaj czas wygaśnięcia
    else:
        expire = datetime.now() + timedelta(minutes=15)  # Domyślny czas wygaśnięcia
    to_encode.update({"exp": expire})  # Dodaj datę wygaśnięcia do tokena
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # Zakoduj JWT
    return encoded_jwt

######## ENDPOINTY ########
# Endpoint do rejestracji użytkownika
@app.post("/register/")
async def register_user(user_data: UserCreate, db: SessionLocal = Depends(get_db)):
    # Sprawdź, czy użytkownik z podanym emailem już istnieje
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Haszuj hasło użytkownika
    hashed_password = get_password_hash(user_data.password)
    
    # Tworzenie nowego użytkownika w bazie danych
    new_user = User(
        name=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    db.add(new_user)  # Dodaj nowego użytkownika do sesji
    db.commit()  # Zatwierdź zmiany w bazie danych
    db.refresh(new_user)  # Odśwież dane użytkownika
    
    # Zwróć komunikat potwierdzenia
    return {"msg": "User registered successfully"}

# Endpoint do logowania i uzyskiwania tokena JWT
@app.post("/login/", response_model=Token)
async def login(user_data: UserCreate, db: SessionLocal = Depends(get_db)):
    # Szukaj użytkownika w bazie danych na podstawie emaila
    db_user = db.query(User).filter(User.email == user_data.email).first()
    
    # Jeśli użytkownik nie istnieje lub hasło jest nieprawidłowe, zwróć błąd
    if not db_user or not verify_password(user_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generowanie tokenu JWT po poprawnym logowaniu
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    
    # Zwróć token JWT
    return {"access_token": access_token, "token_type": "bearer"}

# Funkcja główna uruchamiająca serwer
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
