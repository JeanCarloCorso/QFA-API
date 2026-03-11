from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class MacroProjections(BaseModel):
    selic_esperada: float = Field(..., ge=0.0, le=100.0, description="Taxa Selic esperada em %")
    ipca_esperado: float = Field(..., ge=-20.0, le=100.0, description="IPCA esperado em %")
    pib_esperado: float = Field(..., ge=-20.0, le=50.0, description="Crescimento do PIB esperado em %")

class HorizonScore(BaseModel):
    ano_1: float = Field(..., ge=0, le=10)
    ano_2: float = Field(..., ge=0, le=10)
    ano_5: float = Field(..., ge=0, le=10)
    ano_10: float = Field(..., ge=0, le=10)

class RiskFlags(BaseModel):
    bankruptcy_risk: bool
    manipulation_risk: bool

class AnalysisResultBase(BaseModel):
    global_score: Optional[float] = None
    scores: Optional[HorizonScore] = None
    flags: Optional[RiskFlags] = None
    raw_data_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
