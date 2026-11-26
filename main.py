import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt

# Lê as variáveis do arquivo .env
load_dotenv()

# CRIAR TOKEN JWT

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

#Se não exister a chave o servidor avisa na hora

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY não encontrada. Crie o .env")



def criar_token(email: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=30)
    dados = {"sub": email, "exp": expira}
    return jwt.encode(dados, SECRET_KEY, algorithm=ALGORITHM)


app = FastAPI(title="API de Autenticação")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Usuários salvos na memória
usuarios = []


# Define o que o cadastro (/auth/register) exige: o FastAPI valida os dados antes da função rodar
class UsuarioCadastro(BaseModel):
    email: EmailStr
    senha: str


class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str


@app.get("/")
def raiz():
    return {"Mensagem": "API de autenticação está funcionando"}


@app.post("/auth/register", status_code=201)
def cadastrar(dados: UsuarioCadastro):
    for u in usuarios:
        if u["email"] == dados.email:
            raise HTTPException(status_code=400, detail="Email já cadastrado")

    usuarios.append({
        "email": dados.email,
        "senha_hash": pwd_context.hash(dados.senha),
    })
    return {"Mensagem": "Usuário criado!"}


@app.post("/auth/login")
def login(dados: UsuarioLogin):
    for ul in usuarios:
        if ul["email"] == dados.email and pwd_context.verify(dados.senha, ul["senha_hash"]):
            return {"access_token": criar_token(dados.email), "token_type": "bearer"}

    raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")