import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import Base, app, get_db

# Banco só para os testes, na memória: o usuarios.db de verdade não é tocado
engine_teste = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionTeste = sessionmaker(bind=engine_teste)


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine_teste)

    def get_db_teste():
        db = SessionTeste()
        try:
            yield db
        finally:
            db.close()

    # Troca o banco real pelo banco de teste
    app.dependency_overrides[get_db] = get_db_teste
    yield TestClient(app)

    # Limpa tudo depois de cada teste
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_teste)


def test_cadastro_com_sucesso(client):
    resposta = client.post(
        "/auth/register",
        json={"email": "teste@email.com", "senha": "minhasenha123"},
    )
    assert resposta.status_code == 201

def test_cadastro_email_duplicado(client):
    dados = {"email": "teste@email.com", "senha": "minhasenha123"}

    client.post("/auth/register", json=dados)  # 1º cadastro
    resposta = client.post(
        "/auth/register",
        json=dados,
    )
    assert resposta.status_code == 400

def test_login_com_sucesso(client):
    dados = {"email": "teste@gmail.com", "senha": "minhasenha123"}

    client.post("/auth/register", json=dados)
    resposta = client.post(
        "/auth/login",
        json=dados,
    )

    assert resposta.status_code == 200
    assert "access_token" in resposta.json()
