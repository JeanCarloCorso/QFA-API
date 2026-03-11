from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class CompanyBase(BaseModel):
    ticker: str = Field(..., max_length=20, description="O ticker do ativo na bolsa (ex: WEGE3.SA)")
    company_name: str = Field(..., max_length=255, description="Nome oficial ou razão social da empresa")
    sector: str = Field(..., max_length=100, description="Setor principal de atuação estrutural")
    subsector: str = Field(..., max_length=100, description="Subsetor específico ou nicho de mercado")

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    ticker: Optional[str] = Field(None, max_length=20)
    company_name: Optional[str] = Field(None, max_length=255)
    sector: Optional[str] = Field(None, max_length=100)
    subsector: Optional[str] = Field(None, max_length=100)

class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
