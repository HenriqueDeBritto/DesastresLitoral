# -*- coding: utf-8 -*-
"""
ETAPA 03.01 - Filtragem dos municípios da RMVale

Seleciona, na base final do Brasil, os 39 municípios da Região Metropolitana do
Vale do Paraíba e Litoral Norte. O filtro usa a coluna sub_regiao_sp da DTB:
as sub-regiões SR1 a SR5 são exatamente os municípios da RMVale.

Entradas (02_consolidacao_e_merge/saida/):
- municipios_brasil.gpkg
- shapefile/dicionario_colunas_shapefile.csv   (nomes curtos usados no shapefile)
Saídas (03_Filtragem_RM_Vale/saida/):
- shapefile/municipios_rmvale.shp (+ .dbf, .shx, .prj, .cpg)
- shapefile/dicionario_colunas_shapefile.csv
- municipios_rmvale.gpkg
- municipios_rmvale.xlsx   (mesma tabela, sem os polígonos)
"""

import shutil
from pathlib import Path

import geopandas as gpd
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PASTA_ETAPA_02 = RAIZ / "02_consolidacao_e_merge" / "saida"
PASTA_SAIDA = Path(__file__).resolve().parent / "saida"
PASTA_SHAPEFILE = PASTA_SAIDA / "shapefile"
PASTA_SHAPEFILE.mkdir(parents=True, exist_ok=True)

ARQ_BRASIL = PASTA_ETAPA_02 / "municipios_brasil.gpkg"
ARQ_DICIONARIO_BRASIL = PASTA_ETAPA_02 / "shapefile" / "dicionario_colunas_shapefile.csv"

ARQ_SHP = PASTA_SHAPEFILE / "municipios_rmvale.shp"
ARQ_DICIONARIO = PASTA_SHAPEFILE / "dicionario_colunas_shapefile.csv"
ARQ_GPKG = PASTA_SAIDA / "municipios_rmvale.gpkg"
ARQ_XLSX = PASTA_SAIDA / "municipios_rmvale.xlsx"

SUB_REGIOES_RMVALE = ["SR1", "SR2", "SR3", "SR4", "SR5"]
TOTAL_MUNICIPIOS_RMVALE = 39

# -----------------------------------------------------------------------------
# 1. Leitura e filtro
# -----------------------------------------------------------------------------
print("1/3 - Lendo a base do Brasil e filtrando a RMVale...")
gdf = gpd.read_file(ARQ_BRASIL)
gdf_rmvale = gdf[gdf["sub_regiao_sp"].isin(SUB_REGIOES_RMVALE)].copy()

if len(gdf_rmvale) != TOTAL_MUNICIPIOS_RMVALE:
    raise ValueError(
        f"Esperados {TOTAL_MUNICIPIOS_RMVALE} municípios na RMVale, encontrados {len(gdf_rmvale)}. "
        "Confira a coluna sub_regiao_sp da DTB."
    )

gdf_rmvale = gdf_rmvale.sort_values(["sub_regiao_sp", "municipio"]).reset_index(drop=True)

# A leitura do GeoPackage traz como decimal as colunas inteiras que têm vazio no
# Brasil (ex.: v1 = 1.0); no recorte da RMVale elas voltam a ser inteiras
for col in gdf_rmvale.columns.drop("geometry"):
    serie = gdf_rmvale[col]
    if pd.api.types.is_float_dtype(serie) and (serie.dropna() % 1 == 0).all():
        gdf_rmvale[col] = serie.astype("Int64")

# -----------------------------------------------------------------------------
# 2. GeoPackage e tabela Excel (nomes completos)
# -----------------------------------------------------------------------------
print("2/3 - Gravando GeoPackage e tabela Excel...")
gdf_rmvale.to_file(ARQ_GPKG, driver="GPKG")
pd.DataFrame(gdf_rmvale.drop(columns="geometry")).to_excel(ARQ_XLSX, index=False)

# -----------------------------------------------------------------------------
# 3. Shapefile (mesmos nomes curtos da base do Brasil)
# -----------------------------------------------------------------------------
print("3/3 - Gravando shapefile...")
dicionario = pd.read_csv(ARQ_DICIONARIO_BRASIL, sep=";", encoding="utf-8-sig")
mapa = dict(zip(dicionario["nome_completo"], dicionario["nome_shapefile"]))
gdf_rmvale.rename(columns=mapa).to_file(ARQ_SHP, driver="ESRI Shapefile", encoding="UTF-8")
shutil.copyfile(ARQ_DICIONARIO_BRASIL, ARQ_DICIONARIO)

print("\n=======================================================")
print("RECORTE DA RMVALE GERADO COM SUCESSO!")
print(gdf_rmvale["sub_regiao_sp"].value_counts().sort_index().to_string())
print(f"Total: {len(gdf_rmvale)} municípios")
print(f"Shapefile:  {ARQ_SHP}")
print(f"GeoPackage: {ARQ_GPKG}")
print(f"Excel:      {ARQ_XLSX}")
print("=======================================================")
