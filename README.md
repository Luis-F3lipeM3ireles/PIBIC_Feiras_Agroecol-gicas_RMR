# Projeto Feiras Agroecológicas

Análise das feiras agroecológicas da região de Recife/PE: distribuição por
município, bairro e dia da semana, duração das feiras e relação com zona da
cidade e renda dos bairros (Censo 2022).

## Pergunta do projeto

A duração das feiras varia conforme a zona da cidade ou a renda do bairro?

## Fontes de dados

- **PostgreSQL**: tabelas `feiras` e `mapeamento_zonas`.
- **IBGE – bairros (CD2022)**: `PE_bairros_CD2022.ods`.
- **IBGE – Censo 2022, agregados por bairros (domicílio 3)**:
  `Agregados_por_bairros_caracteristicas_domicilio3_BR.csv`
  (V00505 = rendimento médio, V00506 = mediana).
- **GeoJSON dos bairros** (opcional): `bairros_recife_ibge.json`.

## Como configurar

1. Crie e ative o ambiente virtual (Windows):
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
2. Instale as bibliotecas:
   ```
   pip install -r requirements.txt
   ```
3. Crie um arquivo `.env` na pasta do projeto (copie o `.env.example`) e
   preencha a senha do banco.
4. Deixe os arquivos de dados na pasta indicada em `tratamento.py` (`PASTA`).

## Como executar

```
python main.py
```

## Estrutura

| Arquivo | O que faz |
|---|---|
| `conexao.py` | Conexão com o PostgreSQL e consulta das feiras |
| `tratamento.py` | Limpeza dos dados e cruzamento com o IBGE |
| `analise.py` | Estatísticas, testes e gráficos |
| `mapa.py` | Mapa interativo (HTML) |
| `main.py` | Roda tudo na ordem |

## Saídas

Gráficos (`.png`) e o mapa (`.html`) são salvos na pasta do projeto.

## Resultados

_(preencher com 2 ou 3 achados principais e as imagens geradas)_

## Limitações

- Poucas feiras por zona, o que reduz o poder dos testes estatísticos.
- Alguns bairros podem não ter correspondência com a base do IBGE.
- Feiras que acontecem em mais de um dia são contadas pelo primeiro dia na
  análise por dia da semana (heatmap).
