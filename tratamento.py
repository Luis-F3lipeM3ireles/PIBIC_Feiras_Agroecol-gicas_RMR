"""Tratamento dos dados das feiras e cruzamento com os dados do IBGE."""
import re
import unicodedata
from pathlib import Path

import pandas as pd

# Pasta onde estão os arquivos de dados e onde as imagens/mapas serão salvos
PASTA = Path(r"C:\Users\felip\OneDrive\Desktop\Pibic_Feiras_Organicas")

ARQ_IBGE = PASTA / "PE_bairros_CD2022.ods"
ARQ_RENDA = [
    PASTA / "Agregados_por_bairros_caracteristicas_domicilio3_BR.csv",
    PASTA / "Agregados_por_bairros_caracteristicas_domicilio3_BR.csv.csv",
]

# Nomes exatos das colunas do IBGE (altere aqui se mudarem)
COL_BAIRRO_IBGE = "NM_BAIRRO,C,254"
COL_MUN_IBGE = "NM_MUN,C,50"
COL_TESTE_MATCH = "CD_BAIRRO,C,13"

DIAS = {
    1: "Segunda-feira",
    2: "Terça-feira",
    3: "Quarta-feira",
    4: "Quinta-feira",
    5: "Sexta-feira",
    6: "Sábado",
    7: "Domingo",
}


def padronizar_texto(texto):
    """Minúsculas, sem acento e sem espaços nas pontas (para chaves de merge)."""
    if pd.isna(texto):
        return ""
    texto = str(texto).strip().lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def extrair_dia(x):
    if isinstance(x, list) and len(x) > 0:
        return x[0]
    if isinstance(x, str):
        numeros = re.findall(r"\d+", x)
        return int(numeros[0]) if numeros else None
    return x


def tratar_feiras(df):
    """Cria colunas de dia da semana e duração (em horas) da feira."""
    df = df.copy()

    df["dias_semana_texto"] = df["dias_semana"].apply(
        lambda lista: ", ".join(DIAS.get(d, str(d)) for d in lista)
    )
    df["dia_limpo"] = df["dias_semana"].apply(extrair_dia)
    df["dias_semana_nome"] = df["dia_limpo"].map(DIAS)

    inicio = pd.to_datetime(
        df["horario_inicial"].astype(str), format="%H:%M:%S", errors="coerce")
    fim = pd.to_datetime(
        df["horario_final"].astype(str), format="%H:%M:%S", errors="coerce")
    df["duracao_feira"] = (fim - inicio).dt.total_seconds() / 3600

    print("\n---- Dias convertidos ----")
    print(df[["nome_feira", "dias_semana_texto"]].head())
    return df


def integrar_ibge(df):
    """Cruza as feiras com a planilha de bairros do IBGE.

    Se der erro, devolve o df original para o restante do código não quebrar.
    """
    print("\n" + "=" * 50)
    print("📈 CRUZAMENTO COM DADOS DO IBGE")
    print("=" * 50)

    try:
        df_ibge = pd.read_excel(ARQ_IBGE, engine="odf")
        print("✅ Planilha do IBGE carregada com sucesso!")

        df_base = df.copy()
        df_base["bairro_limpo"] = df_base["nome_bairro"].apply(
            padronizar_texto)
        df_base["municipio_limpo"] = df_base["municipio"].apply(
            padronizar_texto)

        df_ibge["bairro_limpo"] = df_ibge[COL_BAIRRO_IBGE].apply(
            padronizar_texto)
        df_ibge["municipio_limpo"] = df_ibge[COL_MUN_IBGE].apply(
            padronizar_texto)

        df_socio = pd.merge(
            df_base,
            df_ibge.drop(columns=[COL_BAIRRO_IBGE,
                         COL_MUN_IBGE], errors="ignore"),
            on=["municipio_limpo", "bairro_limpo"],
            how="left",
        ).drop(columns=["municipio_limpo", "bairro_limpo"])

        print("✅ Cruzamento concluído!")

        sem_match = df_socio[df_socio[COL_TESTE_MATCH].isna()][
            ["municipio", "nome_bairro"]].drop_duplicates()
        if sem_match.empty:
            print("🎉 100% de correspondência entre as feiras e a base do IBGE.")
        else:
            print("⚠️ Bairros sem correspondência no IBGE:")
            print(sem_match)

        return df_socio

    except Exception as e:
        print("❌ Erro ao processar a planilha do IBGE. Seguindo só com dados do banco.")
        print("Detalhes:", e)
        return df.copy()


def integrar_renda(df_socio):
    """Cruza as feiras com a renda real do Censo 2022 (média e mediana).

    Retorna o DataFrame final, ou None se algo falhar.
    """
    print("\n" + "=" * 50)
    print("📊 CRUZAMENTO COM RENDA REAL DO CENSO 2022")
    print("=" * 50)

    try:
        caminho = next((c for c in ARQ_RENDA if c.exists()), ARQ_RENDA[0])
        df_renda = pd.read_csv(
            caminho, sep=";", encoding="iso-8859-1", dtype={"CD_BAIRRO": str})
        print(f"✅ Planilha de renda carregada: {caminho.name}")

        # V00505 = rendimento médio | V00506 = rendimento mediano
        for origem, destino in [("V00505", "RENDA_MEDIA_REAL"),
                                ("V00506", "MEDIANA_RENDA_REAL")]:
            df_renda[destino] = pd.to_numeric(
                df_renda[origem].astype(str).str.replace(",", "."),
                errors="coerce")

        df_renda["bairro_limpo"] = df_renda["NM_BAIRRO"].apply(
            padronizar_texto)
        chaves = ["bairro_limpo"]

        df_base = df_socio.copy()
        df_base["bairro_limpo"] = df_base["nome_bairro"].apply(
            padronizar_texto)

        # O CSV cobre o Brasil todo: se ele tiver a coluna do município,
        # usamos também para não misturar bairros com o mesmo nome em cidades diferentes.
        if "NM_MUN" in df_renda.columns:
            df_renda["municipio_limpo"] = df_renda["NM_MUN"].apply(
                padronizar_texto)
            df_base["municipio_limpo"] = df_base["municipio"].apply(
                padronizar_texto)
            chaves = ["municipio_limpo", "bairro_limpo"]

        colunas = chaves + ["RENDA_MEDIA_REAL", "MEDIANA_RENDA_REAL"]
        df_renda = df_renda[colunas].drop_duplicates(subset=chaves)

        df_final = pd.merge(df_base, df_renda, on=chaves, how="left")
        df_final = df_final.dropna(
            subset=["RENDA_MEDIA_REAL", "MEDIANA_RENDA_REAL", "duracao_feira"])

        print(f"✅ Feiras com dados do Censo: {len(df_final)}")
        return df_final

    except Exception as e:
        print("❌ Erro ao processar os dados de renda do Censo:", e)
        return None
