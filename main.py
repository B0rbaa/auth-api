from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext 

app = FastAPI(title="API de Autenticação")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

#Usuários salvos na memória

usuarios = []

#Define o que o cadastro exige e o FastAPI valida o cadastro(auth/register) antes da função rodar
class UsuarioCadastro(BaseModel):
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

        