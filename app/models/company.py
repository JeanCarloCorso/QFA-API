from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from app.core.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, index=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=False)
    subsector = Column(String(100), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_sector', 'sector'),
        Index('idx_subsector', 'subsector'),
    )
