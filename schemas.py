from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str = Field(..., max_length=72, description="A senha deve ter no máximo 72 caracteres")


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    criado_em: datetime

    class Config:
        from_attributes: True

class CategoriaCreate(BaseModel):
    nome: str
    tipo: str = Field(..., description="Deve ser 'receita' ou 'despesa'")
    usuario_id: int

class CategoriaResponse(BaseModel):
    id: int
    nome: str
    tipo: str
    usuario_id: int

    class Config: 
        from_attribute = True

class TransacaoCreate(BaseModel):
    descricao: str
    valor: float
    tipo: str = Field(..., description="Deve ser 'receita' ou 'despesa'")
    categoria_id: int
    usuario_id: int
    data: Optional[datetime] = None

class TransacaoResponse(BaseModel):
    id: int
    descricao: str
    valor: float
    tipo: str
    data: datetime
    categoria_id: int
    usuario_id: int

    class Config:
        from_attributes = True