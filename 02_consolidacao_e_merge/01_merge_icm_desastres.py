# -*- coding: utf-8 -*-
"""
ETAPA 02.01 - Merge ICM + Desastres (Atlas)

Junta a base do ICM/S2iD (uma linha por município) com os danos dos desastres
sumarizados do Atlas, pelo código IBGE.

Entradas:
- 01_extracao_e_tratamento/saida/01_icm_s2id.xlsx
- 01_extracao_e_tratamento/saida/02_atlas_sumariza.xlsx
Saída:
- 02_consolidacao_e_merge/saida/01_icm_desastres.xlsx
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PASTA_ETAPA_01 = RAIZ / "01_extracao_e_tratamento" / "saida"
PASTA_SAIDA = Path(__file__).resolve().parent / "saida"
PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

ARQ_ICM = PASTA_ETAPA_01 / "01_icm_s2id.xlsx"
ARQ_ATLAS = PASTA_ETAPA_01 / "02_atlas_sumariza.xlsx"
ARQ_SAIDA = PASTA_SAIDA / "01_icm_desastres.xlsx"

# Colunas do Atlas que são SOMA (danos e prejuízos): sem desastre registrado = 0
PREFIXOS_SOMA = ("dh_", "dm_", "pepl_", "pepr_", "pe_")


def sanitizar_coluna(col):
    """snake_case sem acentos nem símbolos (ex.: 'PEPL_Ensino (R$)' -> 'pepl_ensino_reais')"""
    nfkd = unicodedata.normalize("NFKD", str(col))
    col_limpa = "".join([c for c in nfkd if not unicodedata.combining(c)])
    col_limpa = col_limpa.replace("(R$)", "_reais").replace("(r$)", "_reais")
    col_limpa = col_limpa.replace("'", "").replace('"', "")
    col_limpa = re.sub(r"[^a-zA-Z0-9_]", "_", col_limpa)
    col_limpa = re.sub(r"_+", "_", col_limpa)
    return col_limpa.strip("_").lower()


# -----------------------------------------------------------------------------
# 1. Leitura
# -----------------------------------------------------------------------------
print("1/3 - Lendo as bases...")
df_icm = pd.read_excel(ARQ_ICM)
df_atlas = pd.read_excel(ARQ_ATLAS)

df_atlas.columns = [sanitizar_coluna(c) for c in df_atlas.columns]
df_atlas = df_atlas.rename(columns={"cod_ibge_mun": "codigo_ibge"})
df_atlas["codigo_ibge"] = pd.to_numeric(df_atlas["codigo_ibge"], errors="coerce")
df_atlas = df_atlas.dropna(subset=["codigo_ibge"])
df_atlas["codigo_ibge"] = df_atlas["codigo_ibge"].astype(int)

if df_atlas["codigo_ibge"].duplicated().any():
    raise ValueError(
        "O Atlas tem mais de uma linha por município (agrupado por ano?). "
        "Use AGRUPAR_POR_ANO = False na etapa 02_atlas_sumariza.py."
    )

# Nome, UF e região já vêm do ICM
df_atlas = df_atlas.drop(columns=[c for c in ["nome_municipio", "sigla_uf", "regiao"] if c in df_atlas.columns])

# -----------------------------------------------------------------------------
# 2. Merge (outer: nenhum município de nenhuma das bases é perdido)
# -----------------------------------------------------------------------------
print("2/3 - Cruzando ICM + Atlas...")
df_final = df_icm.merge(df_atlas, on="codigo_ibge", how="outer", indicator=True, validate="one_to_one")

so_atlas = df_final.loc[df_final["_merge"] == "right_only", "codigo_ibge"].tolist()
if so_atlas:
    print(f"  [aviso] municípios do Atlas fora do ICM: {so_atlas}")

df_final["possui_registro_atlas"] = (df_final["_merge"] != "left_only").astype(int)
df_final = df_final.drop(columns=["_merge"])

colunas_soma = [c for c in df_atlas.columns if c.startswith(PREFIXOS_SOMA)]
if "qtd_desastres" in df_final.columns:
    colunas_soma.append("qtd_desastres")
df_final[colunas_soma] = df_final[colunas_soma].fillna(0)

# -----------------------------------------------------------------------------
# 3. Salvar
# -----------------------------------------------------------------------------
df_final = df_final.sort_values("codigo_ibge").reset_index(drop=True)
df_final.to_excel(ARQ_SAIDA, index=False)

print("3/3 - Arquivo salvo!")
print(f"  Municípios: {len(df_final)} | com registro no Atlas: {df_final['possui_registro_atlas'].sum()}")
print(f"  Colunas: {len(df_final.columns)}")
print(f"  Caminho: {ARQ_SAIDA}")
