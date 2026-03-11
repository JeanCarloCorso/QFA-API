from sqlalchemy import Column, String, Float, Date, JSON, Index, ForeignKey
import datetime

from app.core.database import Base

class StockEvaluation(Base):
    """
    Tabela principal de armazenamento da nota de Score (Screener).
    Usa o próprio `ticker` como Primary Key (1 avaliação ativa por ação na API),
    limitando os gargalos de junções (joins).
    """
    __tablename__ = "stock_evaluations"

    ticker = Column(String(20), ForeignKey('companies.ticker', ondelete='CASCADE'), primary_key=True, index=True)
    sector = Column(String(100), index=True, nullable=True)
    global_score = Column(Float, index=True, nullable=True)
    full_analysis_json = Column(JSON, nullable=True)
    last_updated = Column(Date, index=True, default=datetime.date.today, onupdate=datetime.date.today)
    selic_used = Column(Float, nullable=True)
    ipca_used = Column(Float, nullable=True)
    pib_used = Column(Float, nullable=True)

    __table_args__ = (
        Index('idx_score_date', 'last_updated', 'global_score'),
    )
