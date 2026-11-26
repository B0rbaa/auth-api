import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

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


#Confere o token

seguranca = HTTPBearer()


def usuario_atual(credenciais: HTTPAuthorizationCredentials = Depends(seguranca)) -> str:
    try:
        dados = jwt.decode(credenciais.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    return dados["sub"]


app = FastAPI(title="API de Autenticação")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Usuários salvos na memória
# Conexão com o arquivo do banco
engine = create_engine("sqlite:///./usuarios.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


# Cada objeto Usuario é uma linha da tabela "usuarios"
class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String)


# Cria a tabela se ela ainda não existir
Base.metadata.create_all(bind=engine)


# Abre uma conexão para cada requisição e fecha no final
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
def cadastrar(dados: UsuarioCadastro, db: Session = Depends(get_db)):
    # 1. Verifica no banco se o e-mail já existe
    usuario_existente = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # 2. Cria o usuário com a senha em hash e salva no banco
    novo_usuario = Usuario(
        email=dados.email,
        senha_hash=pwd_context.hash(dados.senha),
    )
    db.add(novo_usuario)
    db.commit()

    return {"Mensagem": "Usuário criado!"}


@app.post("/auth/login")
def login(dados: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    if usuario and pwd_context.verify(dados.senha, usuario.senha_hash):  # o hash do usuário
        return {"access_token": criar_token(dados.email), "token_type": "bearer"}

    raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

# @app.post("/auth/login")
# def login(dados: UsuarioLogin):
#     for ul in usuarios:
#         if ul["email"] == dados.email and pwd_context.verify(dados.senha, ul["senha_hash"]):
#             return {"access_token": criar_token(dados.email), "token_type": "bearer"}

#     raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")

@app.get("/users/me")
def perfil(email: str = Depends(usuario_atual)):
    return {"email": email}
