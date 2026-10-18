"""Conexão com o PostgreSQL e carga dos dados das feiras.

As credenciais ficam no arquivo .env (nunca no código).
"""
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

QUERY_FEIRAS = """
SELECT
    f.nome_feira,
    f.municipio,
    f.nome_bairro,
    z.zona,
    f.dias_semana,
    f.horario_inicial,
    f.horario_final,
    f.latitude,
    f.longitude
FROM feiras f
LEFT JOIN mapeamento_zonas z
    ON f.nome_bairro = z.nome_bairro;
"""


def get_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME", "postgres"),
    )
    return create_engine(url)


def testar_conexao():
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Conexão realizada com sucesso!")
        return True
    except UnicodeDecodeError as erro:
        # O Postgres respondeu em português (Windows) e o Python não decodificou.
        # Aqui lemos os bytes originais da mensagem.
        print("❌ Erro ao conectar. Mensagem do Postgres:")
        print(erro.object.decode("latin-1", errors="replace"))
        return False
    except Exception as erro:
        print("❌ Erro ao conectar:", erro)
        return False


def carregar_feiras():
    df = pd.read_sql(QUERY_FEIRAS, get_engine())
    print("--- Primeiras linhas dos dados ---")
    print(df.head())
    return df
