"""Ponto de entrada: roda o fluxo completo na ordem.

Executar com:  python main.py
"""
import analise
from conexao import carregar_feiras, testar_conexao
from mapa import gerar_mapa
from tratamento import integrar_ibge, integrar_renda, tratar_feiras


def main():
    # 1. Banco de dados
    if not testar_conexao():
        return
    df = tratar_feiras(carregar_feiras())

    # 2. Análises das feiras
    analise.analise_qualitativa(df)
    analise.analise_duracao(df)
    analise.testes_normalidade(df)
    analise.kruskal_zonas(df)

    # 3. Integração com o IBGE
    df_socio = integrar_ibge(df)
    analise.analise_territorial(df_socio)
    gerar_mapa(df_socio)

    # 4. Renda real do Censo 2022
    df_final = integrar_renda(df_socio)
    if df_final is not None:
        analise.correlacao_renda(df_final)


if __name__ == "__main__":
    main()
