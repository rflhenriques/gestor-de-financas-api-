import os
from datetime import datetime, timedelta
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# Importações locais
import models
import schemas
from database import SessionLocal, engine

# Carrega as variáveis do arquivo .env
load_dotenv()

# ==========================================
# CONFIGURAÇÕES DE SEGURANÇA
# ==========================================
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ==========================================
# APP E DEPENDÊNCIAS
# ==========================================
app = FastAPI(
    title="API - Gestor de Finanças",
    description="Sistema completo com CRUD e Autenticação JWT",
    version="2.0.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() # Corrigido: adicionado ()

# ==========================================
# FUNÇÕES AUXILIARES (LÓGICA)
# ==========================================

def criar_token_acesso(data: dict):
    """Gera o Token JWT de acesso."""
    dados_para_criptografar = data.copy()
    # Corrigido: utcnow() com parênteses
    expiracao = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dados_para_criptografar.update({"exp": expiracao})
    return jwt.encode(dados_para_criptografar, SECRET_KEY, algorithm=ALGORITHM)

def obter_usuario_atual(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """Valida o Token e identifica o usuário logado."""
    erro_credenciais = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise erro_credenciais
    except JWTError:
        raise erro_credenciais

    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if usuario is None:
        raise erro_credenciais
    
    return usuario

# ==========================================
# ROTAS DE AUTENTICAÇÃO (LOGIN)
# ==========================================

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Gera a chave de acesso (Token) para o usuário."""
    usuario = db.query(models.Usuario).filter(models.Usuario.email == form_data.username).first()

    # Corrigido: usando senha_hash para bater com o models.py
    if not usuario or not pwd_context.verify(form_data.password, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos.")
    
    token_acesso = criar_token_acesso(data={"sub": usuario.email})
    return {"access_token": token_acesso, "token_type": "bearer"}

# ==========================================
# ROTAS DE USUÁRIOS
# ==========================================

@app.post("/usuarios", response_model=schemas.UsuarioResponse)
def criar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="Este email já está cadastrado.")
    
    senha_criptografada = pwd_context.hash(usuario.senha)
    novo_usuario = models.Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=senha_criptografada # Corrigido: nome da coluna
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

@app.get("/usuarios/", response_model=List[schemas.UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(models.Usuario).all()

# ==========================================
# ROTAS DE CATEGORIAS
# ==========================================

@app.post("/categoria/", response_model=schemas.CategoriaResponse)
def criar_categoria(categoria: schemas.CategoriaCreate, db: Session = Depends(get_db)):
    usuario_existe = db.query(models.Usuario).filter(models.Usuario.id == categoria.usuario_id).first()
    if not usuario_existe:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    nova_categoria = models.Categoria(**categoria.model_dump())
    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)
    return nova_categoria

@app.get("/categorias/{usuario_id}", response_model=List[schemas.CategoriaResponse])
def listar_categorias_do_usuario(usuario_id: int, db: Session = Depends(get_db)):
    return db.query(models.Categoria).filter(models.Categoria.usuario_id == usuario_id).all()

# ==========================================
# ROTAS DE TRANSAÇÕES (CRUD)
# ==========================================

@app.post("/transacoes/", response_model=schemas.TransacaoResponse)
def criar_transacao(transacao: schemas.TransacaoCreate, db: Session = Depends(get_db)):
    # Validações de existência
    if not db.query(models.Usuario).filter(models.Usuario.id == transacao.usuario_id).first():
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if not db.query(models.Categoria).filter(models.Categoria.id == transacao.categoria_id).first():
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    dados_transacao = transacao.model_dump()
    if not dados_transacao.get("data"):
        dados_transacao["data"] = datetime.utcnow()
    
    nova_transacao = models.Transacao(**dados_transacao)
    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)
    return nova_transacao

@app.get("/transacoes/{usuario_id}", response_model=List[schemas.TransacaoResponse])
def listar_transacoes_do_usuario(usuario_id: int, db: Session = Depends(get_db)):
    return db.query(models.Transacao).filter(models.Transacao.usuario_id == usuario_id).all()

@app.put("/transacoes/{transacao_id}", response_model=schemas.TransacaoResponse)
def atualizar_transacao(transacao_id: int, transacao_atualizada: schemas.TransacaoCreate, db: Session = Depends(get_db)):
    transacao_db = db.query(models.Transacao).filter(models.Transacao.id == transacao_id).first()
    if not transacao_db:
        raise HTTPException(status_code=404, detail="Transação não encontrada.")
    
    dados = transacao_atualizada.model_dump()
    for key, value in dados.items(): # Corrigido: de itens() para items()
        setattr(transacao_db, key, value)

    db.commit()
    db.refresh(transacao_db)
    return transacao_db

@app.delete("/transacoes/{transacao_id}")
def deletar_transacao(transacao_id: int, db: Session = Depends(get_db)):
    transacao_db = db.query(models.Transacao).filter(models.Transacao.id == transacao_id).first()
    if not transacao_db:
        raise HTTPException(status_code=404, detail="Transação não encontrada.")
    
    db.delete(transacao_db)
    db.commit()
    return {"mensagem": "Transação excluída com sucesso!"}

# ==========================================
# ROTAS DE RESUMO (COM SEGURANÇA)
# ==========================================

@app.get("/meu-resumo")
def resumo_logado(db: Session = Depends(get_db), usuario_atual: models.Usuario = Depends(obter_usuario_atual)):
    """Retorna o resumo financeiro apenas do dono do Token."""
    transacoes = db.query(models.Transacao).filter(models.Transacao.usuario_id == usuario_atual.id).all()

    total_receitas = sum(t.valor for t in transacoes if t.tipo == "receita")
    total_despesas = sum(t.valor for t in transacoes if t.tipo == "despesa")
    
    return {
        "usuario": usuario_atual.nome,
        "email": usuario_atual.email,
        "total_receitas": total_receitas,
        "total_despesas": total_despesas,
        "saldo_atual": total_receitas - total_despesas
    }

# ==========================================
# TRANSAÇÕES PROTEGIDAS (SÓ O DONO ACESSA)
# ==========================================

@app.post("/transacoes/", response_model=schemas.TransacaoResponse)
def criar_transacao_protegida(
    transacao: schemas.TransacaoCreate, 
    db: Session = Depends(get_db), 
    usuario_atual: models.Usuario = Depends(obter_usuario_atual)
):
    """Cria uma transação vinculada AUTOMATICAMENTE ao usuário logado."""
    
    # 1. Verificamos se a categoria existe
    categoria_existe = db.query(models.Categoria).filter(models.Categoria.id == transacao.categoria_id).first()
    if not categoria_existe:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    # 2. IGNORAMOS o usuario_id que vem no JSON e forçamos o ID do Token
    dados_transacao = transacao.model_dump()
    dados_transacao["usuario_id"] = usuario_atual.id # Segurança total aqui
    
    if not dados_transacao.get("data"):
        dados_transacao["data"] = datetime.utcnow()
    
    nova_transacao = models.Transacao(**dados_transacao)
    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)
    return nova_transacao

@app.get("/transacoes/", response_model=list[schemas.TransacaoResponse])
def listar_minhas_transacoes(
    db: Session = Depends(get_db), 
    usuario_atual: models.Usuario = Depends(obter_usuario_atual)
):
    """Lista apenas as transações do usuário dono do Token."""
    # O filtro agora é automático pelo ID do token
    return db.query(models.Transacao).filter(models.Transacao.usuario_id == usuario_atual.id).all()