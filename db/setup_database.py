import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()


def normalize_pg_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+psycopg2" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def ensure_db_name_safe(db_name: str) -> str:
    if not db_name.replace("_", "").isalnum():
        raise ValueError("DB_NAME solo puede tener letras, numeros y underscore.")
    return db_name


def admin_url_from_database_url(database_url: str) -> str:
    parsed = urlsplit(database_url)
    return urlunsplit((parsed.scheme, parsed.netloc, "/", parsed.query, parsed.fragment))


def main():
    db_name = ensure_db_name_safe(os.getenv("DB_NAME", "fleet_portfolio_ml"))

    database_url_env = os.getenv("DATABASE_URL", "").strip()
    admin_url_env = os.getenv("DB_ADMIN_URL", "").strip()

    if not admin_url_env and not database_url_env:
        raise ValueError("Define DB_ADMIN_URL o DATABASE_URL en tu .env")

    if not admin_url_env:
        admin_url_env = admin_url_from_database_url(database_url_env)

    admin_url = normalize_pg_url(admin_url_env)

    if not database_url_env:
        database_url_env = admin_url_env.rstrip("/") + f"/{db_name}"
    database_url = normalize_pg_url(database_url_env)

    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
            print(f"Base de datos creada: {db_name}")
        else:
            print(f"Base de datos ya existe: {db_name}")

    schema_path = Path("db/001_schema.sql")
    sql = schema_path.read_text(encoding="utf-8-sig")

    app_engine = create_engine(database_url, isolation_level="AUTOCOMMIT")
    with app_engine.connect() as conn:
        conn.exec_driver_sql(sql)

    print(f"Esquema aplicado en: {database_url_env}")


if __name__ == "__main__":
    main()
