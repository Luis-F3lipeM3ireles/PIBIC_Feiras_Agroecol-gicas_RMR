"""Dashboard interativo das feiras agroecológicas.

Executar, a partir da pasta do projeto:
    streamlit run dashboard/app.py
"""
from tratamento import DIAS, tratar_feiras
from conexao import carregar_feiras
from streamlit_folium import st_folium
import streamlit as st
import plotly.express as px
import pandas as pd
import folium
import sys
from pathlib import Path

# Permite importar conexao.py e tratamento.py, que ficam na pasta acima
sys.path.append(str(Path(__file__).resolve().parent.parent))


CENTRO_RECIFE = [-8.05428, -34.8813]

st.set_page_config(page_title="Feiras Agroecológicas",
                   page_icon="🥬", layout="wide")


@st.cache_data
def carregar_dados():
    df = tratar_feiras(carregar_feiras())
    df["zona"] = df["zona"].fillna("Sem zona")
    return df


df = carregar_dados()

# ---------------------------------------------------------------
# FILTROS (barra lateral)
# ---------------------------------------------------------------
st.sidebar.header("Filtros")

zonas = ["Todas"] + sorted(df["zona"].unique())
zona_escolhida = st.sidebar.selectbox("Região (zona)", zonas)

dias_opcoes = ["Todos"] + list(DIAS.values())
dia_escolhido = st.sidebar.selectbox("Dia da semana", dias_opcoes)

# Aplicando os filtros
df_zona = df if zona_escolhida == "Todas" else df[df["zona"] == zona_escolhida]

if dia_escolhido == "Todos":
    df_filtrado = df_zona
else:
    numero_dia = [n for n, nome in DIAS.items() if nome == dia_escolhido][0]
    # Uma feira pode acontecer em vários dias: vale se o dia está na lista dela
    df_filtrado = df_zona[df_zona["dias_semana"].apply(
        lambda lista: numero_dia in lista)]

# ---------------------------------------------------------------
# CONTEÚDO
# ---------------------------------------------------------------
st.title("🥬 Feiras Agroecológicas")
st.caption(f"Região: {zona_escolhida} | Dia: {dia_escolhido}")

if df_filtrado.empty:
    st.warning("Nenhuma feira encontrada com esses filtros.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Feiras encontradas", len(df_filtrado))
col2.metric("Bairros", df_filtrado["nome_bairro"].nunique())
duracao_media = df_filtrado["duracao_feira"].mean()
col3.metric("Duração média (h)",
            f"{duracao_media:.1f}" if pd.notna(duracao_media) else "N/A")

aba_mapa, aba_graficos, aba_tabela = st.tabs(
    ["🗺️ Mapa", "📊 Gráficos", "📋 Tabela"])

with aba_mapa:
    com_coord = df_filtrado.dropna(subset=["latitude", "longitude"])
    if com_coord.empty:
        st.info("Nenhuma feira com coordenadas para mostrar no mapa.")
    else:
        centro = [com_coord["latitude"].astype(float).mean(),
                  com_coord["longitude"].astype(float).mean()]
        mapa = folium.Map(location=centro or CENTRO_RECIFE,
                          zoom_start=12, tiles="cartodbpositron")
        for _, linha in com_coord.iterrows():
            texto = (
                f"<b>{linha['nome_feira']}</b><br>"
                f"Bairro: {linha['nome_bairro']}<br>"
                f"Zona: {linha['zona']}<br>"
                f"Dias: {linha['dias_semana_texto']}<br>"
                f"Duração: {linha['duracao_feira']:.1f} h"
            )
            folium.Marker(
                location=[float(linha["latitude"]), float(linha["longitude"])],
                popup=folium.Popup(texto, max_width=300),
                tooltip=linha["nome_feira"],
                icon=folium.Icon(
                    color="green", icon="shopping-cart", prefix="fa"),
            ).add_to(mapa)
        st_folium(mapa, height=500, use_container_width=True)

with aba_graficos:
    esquerda, direita = st.columns(2)

    # Feiras por dia da semana (usa só o filtro de região, para comparar os dias)
    por_dia = (df_zona["dias_semana"].explode().map(DIAS)
               .value_counts().reindex(list(DIAS.values()), fill_value=0)
               .reset_index())
    por_dia.columns = ["Dia", "Feiras"]
    esquerda.plotly_chart(
        px.bar(por_dia, x="Dia", y="Feiras", title="Feiras por dia da semana"),
        use_container_width=True)

    direita.plotly_chart(
        px.histogram(df_filtrado, x="duracao_feira", nbins=10,
                     title="Distribuição da duração (horas)",
                     labels={"duracao_feira": "Duração (h)"}),
        use_container_width=True)

    por_bairro = df_filtrado["nome_bairro"].value_counts().reset_index()
    por_bairro.columns = ["Bairro", "Feiras"]
    st.plotly_chart(
        px.bar(por_bairro, x="Feiras", y="Bairro", orientation="h",
               title="Feiras por bairro"),
        use_container_width=True)

with aba_tabela:
    st.dataframe(
        df_filtrado[["nome_feira", "municipio", "nome_bairro", "zona",
                    "dias_semana_texto", "horario_inicial",
                     "horario_final", "duracao_feira"]],
        use_container_width=True, hide_index=True)
