"""Análises qualitativas, estatísticas e gráficos."""
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from scipy import stats
from scipy.stats import kstest, norm, shapiro

from tratamento import DIAS, PASTA

COL_DISTRITO = "NM_DIST,C,50"
COL_CONURB = "NM_CONCURB,C,254"

sns.set_theme(style="whitegrid")


def _salvar_e_mostrar(nome_arquivo):
    plt.tight_layout()
    plt.savefig(PASTA / nome_arquivo, dpi=300)
    plt.show()


def _titulo(texto):
    print("\n" + "=" * 50)
    print(texto)
    print("=" * 50)


# ---------------------------------------------------------------
# ANÁLISE QUALITATIVA
# ---------------------------------------------------------------
def analise_qualitativa(df):
    feiras_por_municipio = df["municipio"].value_counts()
    print("👉 QUANTIDADE DE FEIRAS POR MUNICÍPIO:")
    print(feiras_por_municipio)

    bairros_percentual = (
        df.groupby("municipio")["nome_bairro"].value_counts(
            normalize=True) * 100
    )
    print("\n👉 % DE CONCENTRAÇÃO DE FEIRAS POR BAIRRO:")
    print(bairros_percentual.round(2).astype(str) + "%")

    dias_percentual = df["dias_semana"].explode().map(DIAS).value_counts(
        normalize=True) * 100
    print("\n👉 DIAS DA SEMANA MAIS POPULARES (%):")
    print(dias_percentual.round(2).astype(str) + "%")

    plt.figure(figsize=(10, 6))
    sns.barplot(x=feiras_por_municipio.index, y=feiras_por_municipio.values)
    plt.title("Quantidade de Feiras por Município")
    plt.xlabel("Município")
    plt.ylabel("Quantidade de Feiras")
    plt.xticks(rotation=45)
    _salvar_e_mostrar("feiras_por_municipio.png")

    plt.figure(figsize=(10, 6))
    bairros_percentual.sort_values(ascending=False).plot(kind="barh")
    plt.title("% de Concentração de Feiras por Bairro")
    plt.xlabel("Percentual (%)")
    plt.ylabel("Bairro")
    _salvar_e_mostrar("percentual_por_bairro.png")

    plt.figure(figsize=(7, 7))
    dias_percentual.plot(kind="pie", autopct="%1.1f%%")
    plt.title("Dias da Semana Mais Populares (%)")
    plt.ylabel("")
    _salvar_e_mostrar("dias_populares.png")


# ---------------------------------------------------------------
# ANÁLISE QUANTITATIVA: DURAÇÃO DAS FEIRAS
# ---------------------------------------------------------------
def analise_duracao(df):
    serie = df["duracao_feira"]
    media, mediana = serie.mean(), serie.median()
    moda_series = serie.mode()
    moda = f"{moda_series[0]:.2f}" if not moda_series.empty else "N/A"

    _titulo("👉 MEDIDAS DE TENDÊNCIA CENTRAL (DURAÇÃO)")
    print(f"Média de Duração:   {media:.2f} horas")
    print(f"Mediana de Duração: {mediana:.2f} horas")
    print(f"Moda de Duração:    {moda} horas")

    _titulo("👉 MEDIDAS DE DISPERSÃO (DURAÇÃO)")
    print(f"Desvio Padrão:   {serie.std():.2f} horas")
    print(f"Variância:       {serie.var():.2f}")
    print(f"Duração Mínima:  {serie.min():.2f} horas")
    print(f"Duração Máxima:  {serie.max():.2f} horas")
    print(f"Amplitude Total: {serie.max() - serie.min():.2f} horas")

    _titulo("👉 RESUMO ESTATÍSTICO (.describe())")
    print(serie.describe())

    plt.figure(figsize=(10, 5))
    sns.histplot(data=df, x="duracao_feira", kde=True, color="teal", bins=10)
    plt.axvline(media, color="red", linestyle="--", linewidth=2,
                label=f"Média: {media:.2f}h")
    plt.axvline(mediana, color="orange", linestyle="-", linewidth=2,
                label=f"Mediana: {mediana:.2f}h")
    plt.title("Distribuição da Duração das Feiras Agroecológicas")
    plt.xlabel("Duração (em horas)")
    plt.ylabel("Quantidade de Feiras")
    plt.legend()
    _salvar_e_mostrar("distribuicao_duracao_feiras.png")

    plt.figure(figsize=(8, 4))
    sns.boxplot(data=df, x="duracao_feira", color="lightgreen", width=0.4)
    plt.title("Boxplot - Dispersão e Quartis da Duração")
    plt.xlabel("Duração (em horas)")
    _salvar_e_mostrar("boxplot_duracao_feiras.png")


def testes_normalidade(df):
    dados = df["duracao_feira"].dropna()

    stat_sw, p_sw = shapiro(dados)
    print(f"Shapiro-Wilk: estatística = {stat_sw:.4f}, p-valor = {p_sw:.4f}")

    stat_ks, p_ks = kstest(dados, norm(
        loc=dados.mean(), scale=dados.std()).cdf)
    print(
        f"Kolmogorov-Smirnov: estatística = {stat_ks:.4f}, p-valor = {p_ks:.4f}")

    sm.qqplot(dados, line="s")
    plt.title("Q-Q Plot - Teste de Normalidade")
    plt.show()


def kruskal_zonas(df):
    df_limpo = df[["duracao_feira", "zona"]].dropna()
    grupos = [g["duracao_feira"].values for _, g in df_limpo.groupby("zona")]

    _titulo("Teste de Kruskal-Wallis (COMPARAÇÃO POR ZONAS)")
    h, p = stats.kruskal(*grupos)
    print(f"Estatística H = {h:.4f}")
    print(f"p-valor       = {p:.4f}")

    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df_limpo, x="zona", y="duracao_feira",
                palette="Set2", hue="zona", legend=False)
    sns.stripplot(data=df_limpo, x="zona", y="duracao_feira",
                  color="black", alpha=0.3, size=5, jitter=True)
    plt.title(
        f"Duração das Feiras por Zona\n(Kruskal-Wallis: H = {h:.2f}, p-valor = {p:.4f})")
    plt.xlabel("Zonas da Cidade")
    plt.ylabel("Duração (em horas)")
    plt.xticks(rotation=15)
    _salvar_e_mostrar("kruskal_wallis_zonas.png")


# ---------------------------------------------------------------
# ANÁLISE TERRITORIAL (IBGE)
# ---------------------------------------------------------------
def analise_territorial(df_socio):
    if COL_DISTRITO not in df_socio.columns:
        print("ℹ️ Colunas do IBGE ausentes: análise territorial ignorada.")
        return

    _titulo("🔍 CENTRALIDADE E MALHA METROPOLITANA")

    print("\n👉 FEIRAS POR DISTRITO (IBGE):")
    print(df_socio[COL_DISTRITO].value_counts())

    if COL_CONURB in df_socio.columns:
        print("\n👉 DISTRIBUIÇÃO POR ARRANJO URBANO / CONURBAÇÃO:")
        print(df_socio[COL_CONURB].value_counts())

    duracao = (df_socio.groupby(COL_DISTRITO)["duracao_feira"]
               .mean().sort_values(ascending=False))
    print("\n👉 DURAÇÃO MÉDIA POR DISTRITO (HORAS):")
    print(duracao.round(2).astype(str) + " horas")

    plt.figure(figsize=(12, 6))
    matriz = pd.crosstab(df_socio[COL_DISTRITO], df_socio["dias_semana_nome"])
    sns.heatmap(matriz, annot=True, cmap="YlGnBu", fmt="d", cbar=True)
    plt.title("Concentração de Feiras por Distrito e Dia da Semana")
    plt.xlabel("Dia da Semana")
    plt.ylabel("Distrito (IBGE)")
    _salvar_e_mostrar("heatmap_territorial_tempo.png")


# ---------------------------------------------------------------
# RENDA REAL DO CENSO 2022 x DURAÇÃO
# ---------------------------------------------------------------
def _spearman_renda(df, coluna, rotulo, paleta, arquivo):
    print(f"\n--- [{rotulo.upper()}] ---")

    plt.figure(figsize=(10, 5))
    sns.scatterplot(data=df, x=coluna, y="duracao_feira",
                    hue="zona", s=150, palette=paleta)
    plt.title(f"Duração da Feira vs {rotulo} do Bairro (Censo 2022)")
    plt.xlabel(f"{rotulo} (R$)")
    plt.ylabel("Duração da Feira (Horas)")
    _salvar_e_mostrar(arquivo)

    corr, p = stats.spearmanr(df[coluna], df["duracao_feira"])
    print(f"📊 Spearman = {corr:.4f}")
    print(f"📉 p-valor  = {p:.4f}")
    if p < 0.05:
        print("📢 Resultado estatisticamente significativo.")
    else:
        print("📢 Sem significância estatística.")


def correlacao_renda(df_final):
    _titulo("📊 INVESTIGAÇÃO SOCIOECONÔMICA (CENSO 2022)")
    _spearman_renda(df_final, "RENDA_MEDIA_REAL", "Rendimento médio",
                    "Set1", "dispersao_renda_media_real_censo.png")
    _spearman_renda(df_final, "MEDIANA_RENDA_REAL", "Mediana do rendimento",
                    "Set2", "dispersao_mediana_real_censo.png")
