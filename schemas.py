from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

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
        from_attributes = True