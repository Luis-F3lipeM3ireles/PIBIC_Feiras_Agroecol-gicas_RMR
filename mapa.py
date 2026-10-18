"""Mapas da Região Metropolitana do Recife (RMR).

- Mapa interativo (HTML, folium): municípios da RMR + bairros de Recife
  (GeoJSON) + alfinetes das feiras coloridos por zona.
- Imagem estática (PNG, geopandas + matplotlib): mesma informação com design moderno,
  pronta para README, relatório e artigo.
"""
import json
import unicodedata
import webbrowser

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import requests
from folium.plugins import MarkerCluster
from matplotlib.lines import Line2D

from tratamento import PASTA

ARQ_GEOJSON = PASTA / "bairros_recife_ibge.json"
ARQ_MAPA = PASTA / "mapa_geografico_feiras.html"
ARQ_IMAGEM = PASTA / "mapa_rmr_feiras.png"
CENTRO_RMR = [-8.05428, -34.8813]

CAMPO_BAIRRO = "NM_BAIRRO"

LAT_MIN, LAT_MAX = -8.45, -7.60
LON_MIN, LON_MAX = -35.25, -34.75

RMR = {
    "Recife", "Olinda", "Jaboatão dos Guararapes", "Paulista", "Camaragibe",
    "São Lourenço da Mata", "Cabo de Santo Agostinho", "Igarassu",
    "Abreu e Lima", "Araçoiaba", "Ipojuca", "Moreno", "Itapissuma",
    "Ilha de Itamaracá", "Goiana",
}

URL_MUNICIPIOS = ("https://servicodados.ibge.gov.br/api/v1/localidades/"
                  "estados/26/municipios")
URL_MALHA = ("https://servicodados.ibge.gov.br/api/v3/malhas/estados/26"
             "?intrarregiao=municipio&qualidade=minima"
             "&formato=application/vnd.geo+json")

CORES_ZONAS = {
    "Zona Norte": "blue",
    "Zona Sul": "red",
    "Zona Oeste": "orange",
    "Zona Central": "purple",
    "Centro": "purple",
}
DEFAULT_COR = "green"


def normalizar(texto):
    sem_acento = (unicodedata.normalize("NFKD", str(texto))
                  .encode("ascii", "ignore").decode())
    return sem_acento.upper().strip()


def baixar_malha_rmr():
    municipios = requests.get(URL_MUNICIPIOS, timeout=60).json()
    codigos = {str(m["id"]): m["nome"] for m in municipios
               if m["nome"] in RMR}

    geo = requests.get(URL_MALHA, timeout=60).json()
    geo["features"] = [f for f in geo["features"]
                       if f["properties"]["codarea"] in codigos]
    for f in geo["features"]:
        f["properties"]["nome"] = codigos[f["properties"]["codarea"]]
    return geo


# ----------------------------------------------------------------------
# MAPA INTERATIVO (folium)
# ----------------------------------------------------------------------
def camada_rmr(mapa):
    try:
        geo = baixar_malha_rmr()
        print(f"✅ Municípios desenhados: {len(geo['features'])} de {len(RMR)}")

        folium.GeoJson(
            geo,
            name="Região Metropolitana do Recife",
            style_function=lambda x: {
                "fillColor": "#e0f2f1", "color": "#00796b",
                "weight": 1.5, "fillOpacity": 0.15,
            },
            tooltip=folium.GeoJsonTooltip(fields=["nome"],
                                          aliases=["Município:"]),
        ).add_to(mapa)
    except Exception as erro:
        print("⚠️ Não foi possível carregar os municípios da RMR:", repr(erro))


def camada_bairros(mapa, df_socio):
    if not ARQ_GEOJSON.exists():
        print("ℹ️ GeoJSON dos bairros não encontrado.")
        return

    try:
        with open(ARQ_GEOJSON, "r", encoding="utf-8") as f:
            dados_geo = json.load(f)

        for feat in dados_geo["features"]:
            feat["properties"]["bairro_norm"] = normalizar(
                feat["properties"][CAMPO_BAIRRO])

        contagem = (df_socio["nome_bairro"].map(normalizar)
                    .value_counts().reset_index())
        contagem.columns = ["bairro_norm", "quantidade_feiras"]

        folium.Choropleth(
            geo_data=dados_geo,
            name="Densidade de feiras por bairro (Recife)",
            data=contagem,
            columns=["bairro_norm", "quantidade_feiras"],
            key_on="feature.properties.bairro_norm",
            fill_color="YlGnBu",
            fill_opacity=0.5,
            line_opacity=0.3,
            line_color="white",
            legend_name="Quantidade de Feiras por Bairro",
        ).add_to(mapa)
        print("✅ Bairros de Recife coloridos.")
    except Exception as erro:
        print("⚠️ Problema ao renderizar o GeoJSON dos bairros:", repr(erro))


def camada_feiras(mapa, df_socio):
    cluster = MarkerCluster(name="Feiras (Agrupadas)").add_to(mapa)
    total = 0

    for _, linha in df_socio.iterrows():
        lat, lon = linha.get("latitude"), linha.get("longitude")
        if pd.isna(lat) or pd.isna(lon):
            continue
        lat, lon = float(lat), float(lon)

        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            continue

        zona = str(linha.get("zona", "Não informada")).strip()
        duracao = linha.get("duracao_feira", 0)
        duracao = duracao if pd.notna(duracao) else 0
        nome_feira = str(linha.get('nome_feira', 'Sem nome')).strip()
        bairro = str(linha.get('nome_bairro', 'Não informado')).strip()

        popup_html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 13px; width: 220px; line-height: 1.4;">
            <b style="color: #00796b; font-size: 14px;">{nome_feira}</b><hr style="margin: 5px 0; border:0; border-top:1px solid #ccc;">
            <b>📍 Bairro:</b> {bairro}<br>
            <b>🏙️ Zona:</b> {zona}<br>
            <b>⏱️ Duração:</b> {duracao:.1f} horas
        </div>
        """

        cor_icone = CORES_ZONAS.get(zona, DEFAULT_COR)

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=nome_feira,
            icon=folium.Icon(
                color=cor_icone, icon="shopping-basket", prefix="fa"),
        ).add_to(cluster)
        total += 1

    print(f"✅ {total} marcadores estilizados adicionados.")


# ----------------------------------------------------------------------
# IMAGEM ESTÁTICA (geopandas + matplotlib)
# ----------------------------------------------------------------------
def gerar_imagem_rmr(df_socio):
    print("\n" + "=" * 50)
    print("🖼️ GERANDO A IMAGEM MODERNA DA RMR (PNG)")
    print("=" * 50)

    try:
        rmr = gpd.GeoDataFrame.from_features(
            baixar_malha_rmr()["features"], crs="EPSG:4326")
    except Exception as erro:
        print("⚠️ Erro ao baixar malha para imagem:", repr(erro))
        return

    fig, ax = plt.subplots(figsize=(11, 12), facecolor="white")

    rmr.plot(ax=ax, color="#f4f6f4", edgecolor="#b0c4de", linewidth=1.2)

    if ARQ_GEOJSON.exists():
        try:
            bairros = gpd.read_file(ARQ_GEOJSON)
            bairros = (bairros.set_crs("EPSG:4326") if bairros.crs is None
                       else bairros.to_crs("EPSG:4326"))
            bairros["bairro_norm"] = bairros[CAMPO_BAIRRO].map(normalizar)

            contagem = (df_socio["nome_bairro"].map(normalizar)
                        .value_counts().reset_index())
            contagem.columns = ["bairro_norm", "quantidade_feiras"]

            bairros = bairros.merge(contagem, on="bairro_norm", how="left")
            bairros["quantidade_feiras"] = bairros["quantidade_feiras"].fillna(
                0)

            sem_feira = bairros[bairros["quantidade_feiras"] == 0]
            com_feira = bairros[bairros["quantidade_feiras"] > 0]

            sem_feira.plot(ax=ax, color="#eaeaea",
                           edgecolor="white", linewidth=0.5)
            if not com_feira.empty:
                com_feira.plot(
                    ax=ax, column="quantidade_feiras", cmap="YlGnBu",
                    edgecolor="white", linewidth=0.6, legend=True,
                    legend_kwds={
                        "label": "Feiras por bairro (Recife)", "shrink": 0.4},
                )
        except Exception as erro:
            print("⚠️ Erro nos bairros (matplotlib):", repr(erro))

    for _, linha in rmr.iterrows():
        if linha["nome"] == "Recife":
            continue
        ponto = linha.geometry.representative_point()
        ax.annotate(linha["nome"], (ponto.x, ponto.y), ha="center",
                    fontsize=8, fontweight="medium", color="#333333", zorder=4)

    pts = df_socio.copy()
    pts["latitude"] = pd.to_numeric(pts.get("latitude"), errors="coerce")
    pts["longitude"] = pd.to_numeric(pts.get("longitude"), errors="coerce")
    pts = pts.dropna(subset=["latitude", "longitude"])

    if not pts.empty:
        gdf_pts = gpd.GeoDataFrame(
            pts, geometry=gpd.points_from_xy(pts["longitude"], pts["latitude"]), crs="EPSG:4326"
        )
        gdf_pts.plot(ax=ax, color="#d9534f", markersize=40,
                     edgecolor="white", linewidth=0.8, alpha=0.9, zorder=5)

    minx, miny, maxx, maxy = rmr.total_bounds
    margem = 0.03
    ax.set_xlim(minx - margem, maxx + margem)
    ax.set_ylim(miny - margem, maxy + margem)
    ax.set_axis_off()

    ax.set_title("Distribuição Espacial das Feiras na RMR",
                 fontsize=16, fontweight="bold", pad=16, color="#222222")

    ax.legend(
        handles=[Line2D([0], [0], marker="o", color="w",
                        markerfacecolor="#d9534f", markeredgecolor="white",
                        markersize=10, label=f"Feiras ({len(pts)})")],
        loc="lower left", frameon=True, facecolor="white", edgecolor="#cccccc"
    )

    ax.annotate("N", xy=(0.95, 0.97), xytext=(0.95, 0.90),
                xycoords="axes fraction", textcoords="axes fraction",
                ha="center", fontsize=12, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="#333333"))

    fig.text(0.5, 0.02,
             "Fontes: IBGE (malhas territoriais e Censo 2022); Banco de dados do projeto.",
             ha="center", fontsize=8.5, color="#666666")

    fig.savefig(ARQ_IMAGEM, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"✅ Imagem moderna salva em: {ARQ_IMAGEM.resolve()}")


# ----------------------------------------------------------------------
# ENTRADA
# ----------------------------------------------------------------------
def gerar_mapa(df_socio):
    print("\n" + "=" * 50)
    print("🗺️ GERANDO O MAPA GEOGRÁFICO MELHORADO")
    print("=" * 50)

    # Uso do tile Esri World Street Map para evitar bloqueios 403 locais
    mapa = folium.Map(
        location=CENTRO_RMR,
        zoom_start=11,
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (HK), Esri (India), Esri (Korea), and the GIS User Community'
    )

    camada_rmr(mapa)
    camada_bairros(mapa, df_socio)
    camada_feiras(mapa, df_socio)

    folium.LayerControl().add_to(mapa)

    mapa.save(str(ARQ_MAPA))
    print(f"✅ Mapa interativo salvo em: {ARQ_MAPA.resolve()}")

    gerar_imagem_rmr(df_socio)

    webbrowser.open(ARQ_MAPA.resolve().as_uri())
