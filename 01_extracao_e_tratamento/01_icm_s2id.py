# -*- coding: utf-8 -*-
"""
ETAPA 01 - ICM + S2iD

Baixa as 4 planilhas do Indicador de Capacidade Municipal (ICM, faixas A-D) e o
PDF de municípios habilitados no S2iD, unifica tudo em uma linha por município.

Entradas (baixadas automaticamente para dados/downloads/):
- ICM_listaA..D_20260428.xlsx   (gov.br/mdr)
- municipios_habilitados_s2iD_outubro_20211001.pdf   (gov.br/mdr)
Saída:
- 01_extracao_e_tratamento/saida/01_icm_s2id.xlsx
"""

import io
from pathlib import Path

import pandas as pd
import pdfplumber
import requests

# =====================================================================
# CAMINHOS
# =====================================================================
RAIZ = Path(__file__).resolve().parents[1]
PASTA_DOWNLOADS = RAIZ / "dados" / "downloads"
PASTA_SAIDA = Path(__file__).resolve().parent / "saida"
ARQ_SAIDA = PASTA_SAIDA / "01_icm_s2id.xlsx"

PASTA_DOWNLOADS.mkdir(parents=True, exist_ok=True)
PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

URL_BASE = "https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil"
ARQUIVOS_ICM = {
    "A": f"{URL_BASE}/ICM_listaA_20260428.xlsx",
    "B": f"{URL_BASE}/ICM_listaB_20260428.xlsx",
    "C": f"{URL_BASE}/ICM_listaC_20260428.xlsx",
    "D": f"{URL_BASE}/ICM_listaD_20260428.xlsx",
}
URL_PDF_S2ID = (
    f"{URL_BASE}/sistema-integrado-de-informacoes-sobre-desastres/"
    "copy2_of_municipios_habilitados_s2iD_outubro_20211001.pdf"
)
HEADERS_REQ = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def baixar(url, destino):
    """Baixa o arquivo só se ele ainda não existir na pasta de downloads."""
    if destino.exists():
        print(f"  já existe, usando o arquivo local: {destino.name}")
        return
    print(f"  baixando {destino.name}...")
    resp = requests.get(url, headers=HEADERS_REQ, timeout=120)
    resp.raise_for_status()
    destino.write_bytes(resp.content)


# =====================================================================
# PLANILHAS EXCEL - ICM
# =====================================================================
print("\n--- 1/3 PROCESSANDO O ICM (EXCEL) ---")

# Layout das planilhas: 5 linhas de título/cabeçalho e 32 colunas
colunas = (
    ["codigo_ibge", "uf", "codigo_uf", "municipio", "faixa_populacional", "regiao"]
    + [f"v{i}" for i in range(1, 21)]
    + ["porte", "perfil_de_risco", "dimensao_i", "dimensao_ii", "dimensao_iii", "icm_total"]
)

lista_df = []
for faixa, url in ARQUIVOS_ICM.items():
    caminho = PASTA_DOWNLOADS / f"ICM_lista{faixa}_20260428.xlsx"
    baixar(url, caminho)

    df = pd.read_excel(caminho, skiprows=5, header=None, names=colunas)

    # Linhas de rodapé (ex.: "Fonte: Sedec") não têm código IBGE numérico
    df["codigo_ibge"] = pd.to_numeric(df["codigo_ibge"], errors="coerce")
    df = df.dropna(subset=["codigo_ibge"])
    df["codigo_ibge"] = df["codigo_ibge"].astype(int)

    # A faixa do arquivo é a classificação oficial do ICM (A, B, C ou D)
    df["classificacao_icm"] = faixa
    lista_df.append(df)

df_icm = pd.concat(lista_df, ignore_index=True)

colunas_numericas = [f"v{i}" for i in range(1, 21)] + [
    "codigo_uf", "dimensao_i", "dimensao_ii", "dimensao_iii", "icm_total"
]
for col in colunas_numericas:
    df_icm[col] = pd.to_numeric(df_icm[col], errors="coerce").fillna(0).astype(int)

# Conferência: o total da planilha deve ser a soma das três dimensões
soma_dimensoes = df_icm["dimensao_i"] + df_icm["dimensao_ii"] + df_icm["dimensao_iii"]
divergentes = (soma_dimensoes != df_icm["icm_total"]).sum()
if divergentes:
    print(f"  [aviso] {divergentes} municípios com icm_total diferente da soma das dimensões")

if df_icm["codigo_ibge"].duplicated().any():
    raise ValueError("Há códigos IBGE repetidos entre as faixas do ICM.")

print(f"  {len(df_icm)} municípios no ICM")


# =====================================================================
# PDF S2iD
# =====================================================================
print("\n--- 2/3 PROCESSANDO O S2iD (PDF) ---")

caminho_pdf = PASTA_DOWNLOADS / "municipios_habilitados_s2iD_outubro_20211001.pdf"
baixar(URL_PDF_S2ID, caminho_pdf)

dados_tabela = []
with pdfplumber.open(io.BytesIO(caminho_pdf.read_bytes())) as pdf:
    for pagina in pdf.pages:
        tabela = pagina.extract_table()
        if tabela:
            dados_tabela.extend(tabela)

df_s2id = pd.DataFrame(dados_tabela[1:], columns=dados_tabela[0])

# O cabeçalho se repete em cada página; a coluna "Código" traz o código IBGE.
# O cruzamento é feito pelo CÓDIGO (pelo nome erra em municípios homônimos).
col_codigo = next(c for c in df_s2id.columns if str(c).lower().startswith("c"))
codigos_s2id = set(
    pd.to_numeric(df_s2id[col_codigo], errors="coerce").dropna().astype(int)
)
print(f"  {len(codigos_s2id)} municípios habilitados no PDF")


# =====================================================================
# CRUZAMENTO E SAÍDA
# =====================================================================
print("\n--- 3/3 CRUZANDO ICM + S2iD ---")

df_icm["s2id_habilitado"] = df_icm["codigo_ibge"].isin(codigos_s2id).astype(int)

nao_encontrados = codigos_s2id - set(df_icm["codigo_ibge"])
if nao_encontrados:
    print(f"  [aviso] códigos do S2iD fora do ICM: {sorted(nao_encontrados)}")

df_icm.to_excel(ARQ_SAIDA, index=False)

print(f"\nArquivo salvo em: {ARQ_SAIDA}")
print(df_icm["classificacao_icm"].value_counts().sort_index().to_string())
print(f"Habilitados no S2iD: {df_icm['s2id_habilitado'].sum()}")
