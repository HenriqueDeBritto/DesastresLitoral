# -*- coding: utf-8 -*-
"""
ETAPA 03 - Malha municipal do IBGE + DTB (biomas, SIAFI, censo)

Baixa o shapefile oficial dos municípios do IBGE (Malha Municipal 2025) e junta
com a planilha DTB pelo código IBGE. A geometria vem SEMPRE do shapefile do
IBGE: nada de polígono passando por Excel (o limite de 32.767 caracteres por
célula corta os municípios com contorno mais detalhado).

Entradas:
- BR_Municipios_2025.zip   (baixado automaticamente para dados/downloads/)
- dados/entrada/dtb_municipios_biomas_siafi_censo.xlsx
Saída:
- 01_extracao_e_tratamento/saida/03_malha_ibge_dtb.gpkg
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

# =====================================================================
# CAMINHOS
# =====================================================================
RAIZ = Path(__file__).resolve().parents[1]
PASTA_DOWNLOADS = RAIZ / "dados" / "downloads"
PASTA_ENTRADA = RAIZ / "dados" / "entrada"
PASTA_SAIDA = Path(__file__).resolve().parent / "saida"

PASTA_DOWNLOADS.mkdir(parents=True, exist_ok=True)
PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

ANO_MALHA = 2025
URL_MALHA = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    f"malhas_municipais/municipio_{ANO_MALHA}/Brasil/BR_Municipios_{ANO_MALHA}.zip"
)
ARQ_MALHA_ZIP = PASTA_DOWNLOADS / f"BR_Municipios_{ANO_MALHA}.zip"
ARQ_DTB = PASTA_ENTRADA / "dtb_municipios_biomas_siafi_censo.xlsx"
ARQ_SAIDA = PASTA_SAIDA / "03_malha_ibge_dtb.gpkg"

# Lagoa Mirim e Lagoa dos Patos aparecem na malha com código próprio, mas não são municípios
CODIGOS_LAGOAS = [4300001, 4300002]


# =====================================================================
# 1. DOWNLOAD DA MALHA DO IBGE
# =====================================================================
print(f"\n--- 1/3 MALHA MUNICIPAL DO IBGE ({ANO_MALHA}) ---")

if ARQ_MALHA_ZIP.exists():
    print(f"  já existe, usando o arquivo local: {ARQ_MALHA_ZIP.name}")
else:
    print(f"  baixando {ARQ_MALHA_ZIP.name} (~240 MB, pode levar alguns minutos)...")
    with requests.get(URL_MALHA, stream=True, timeout=600) as resp:
        resp.raise_for_status()
        with open(ARQ_MALHA_ZIP, "wb") as f:
            for bloco in resp.iter_content(chunk_size=1024 * 1024):
                f.write(bloco)

municipios = gpd.read_file(f"zip://{ARQ_MALHA_ZIP}!BR_Municipios_{ANO_MALHA}.shp")
municipios["codigo_ibge"] = municipios["CD_MUN"].astype(int)
municipios = municipios[~municipios["codigo_ibge"].isin(CODIGOS_LAGOAS)]

# Da malha ficam só o código e o polígono; os atributos vêm da DTB
municipios = municipios[["codigo_ibge", "geometry"]]
print(f"  {len(municipios)} municípios na malha (CRS {municipios.crs})")


# =====================================================================
# 2. LEITURA DA DTB
# =====================================================================
print("\n--- 2/3 PLANILHA DTB (biomas, SIAFI, censo) ---")

df_dtb = pd.read_excel(ARQ_DTB)
df_dtb["codigo_ibge"] = pd.to_numeric(df_dtb["Cod_Mun"], errors="coerce").astype("Int64")
df_dtb = df_dtb.dropna(subset=["codigo_ibge"]).drop(columns=["Cod_Mun"])
df_dtb["Cod_SIAFI"] = pd.to_numeric(df_dtb["Cod_SIAFI"], errors="coerce").astype("Int64")
print(f"  {len(df_dtb)} municípios na DTB")


# =====================================================================
# 3. CRUZAMENTO (malha manda: todo polígono continua, com ou sem DTB)
# =====================================================================
print("\n--- 3/3 JUNTANDO MALHA + DTB ---")

gdf = municipios.merge(df_dtb, on="codigo_ibge", how="left", validate="one_to_one", indicator=True)

sem_dtb = gdf.loc[gdf["_merge"] == "left_only", "codigo_ibge"].tolist()
sem_poligono = sorted(set(df_dtb["codigo_ibge"]) - set(municipios["codigo_ibge"]))
if sem_dtb:
    print(f"  [aviso] municípios da malha sem linha na DTB: {sem_dtb}")
if sem_poligono:
    print(f"  [aviso] municípios da DTB sem polígono na malha: {sem_poligono}")

gdf = gdf.drop(columns=["_merge"])
gdf = gdf[["codigo_ibge"] + [c for c in gdf.columns if c not in ("codigo_ibge", "geometry")] + ["geometry"]]

gdf.to_file(ARQ_SAIDA, driver="GPKG")
print(f"\nArquivo salvo em: {ARQ_SAIDA}")
print(f"Total de municípios: {len(gdf)}")
