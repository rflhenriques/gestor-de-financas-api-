from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    email = Column(String, unique=True, index=True)
    senha_hash = Column(String)
    criado_em = Column(DateTime, default=datetime.utcnow)

    categorias = relationship("Categoria", back_populates="dono")
    transacoes = relationship("Transacao", back_populates="dono")

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome= Column(String)
    tipo= Column(String)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"))

    dono = relationship("Usuario", back_populates="categorias")
    transacoes = relationship("Transacao", back_populates="categoria")

class Transacao(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String)
    valor = Column(Float)
    tipo = Column(String)
    data = Column(DateTime, default=datetime.utcnow)

    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))

    categoria = relationship("Categoria", back_populates="transacoes")
    dono = relationship("Usuario", back_populates="transacoes")

