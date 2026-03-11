import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from app.core.config import settings

try:
    engine = create_async_engine(
        settings.database_url,
        echo=False,  # True para ver as queries
        pool_pre_ping=True, # Verifica se a conexão com o banco não caiu antes de usar
        pool_size=10,
        max_overflow=20
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    Base = declarative_base()
    
except Exception as e:
    logging.critical(f"Falha ao inicializar o motor de banco de dados: {e}")
    raise

async def get_db_session():
    """
    Dependency (Injeção de dependência) para ser usada nas rotas do FastAPI
    fornecendo uma sessão assíncrona do banco de dados para requests.
    """
    async with AsyncSessionLocal() as session:
        yield session
