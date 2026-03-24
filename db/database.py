import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()


def _normalized_database_url() -> str:
    raw = os.getenv("DATABASE_URL", "").strip()
    env = os.getenv("ENV", "development").lower().strip()

    if not raw:
        if env == "production":
            raise RuntimeError("DATABASE_URL no esta definido en produccion.")
        return "sqlite:///./artifacts/local_dev.db"

    # Soporta errores frecuentes al pegar variables en paneles de despliegue.
    if raw.upper().startswith("DATABASE_URL="):
        raw = raw.split("=", 1)[1].strip()

    if (raw.startswith("\"") and raw.endswith("\"")) or (raw.startswith("'") and raw.endswith("'")):
        raw = raw[1:-1].strip()

    if raw.startswith("${{") and raw.endswith("}}"):
        raise RuntimeError("DATABASE_URL parece una referencia sin resolver (${ {...} }).")

    if raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql+psycopg2://", 1)
    elif raw.startswith("postgresql://") and "+psycopg2" not in raw:
        raw = raw.replace("postgresql://", "postgresql+psycopg2://", 1)

    return raw


DATABASE_URL = _normalized_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
