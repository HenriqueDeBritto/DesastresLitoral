# -*- coding: utf-8 -*-
"""
ETAPA 02.02 - Base final: shapefile com todos os municípios do Brasil

Junta a malha do IBGE + DTB (polígonos) com a base ICM + Desastres pelo
código IBGE e grava o resultado como shapefile e como GeoPackage.

Por que dois formatos?
- Shapefile (.shp): o formato pedido, abre em qualquer SIG. Limita o nome
  das colunas a 10 caracteres, então os nomes são encurtados e o arquivo
  dicionario_colunas_shapefile.csv mostra o nome completo de cada coluna.
- GeoPackage (.gpkg): mesmo conteúdo, com os nomes completos das colunas.

Entradas:
- 01_extracao_e_tratamento/saida/03_malha_ibge_dtb.gpkg
- 02_consolidacao_e_merge/saida/01_icm_desastres.xlsx
Saídas (02_consolidacao_e_merge/saida/):
- shapefile/municipios_brasil.shp (+ .dbf, .shx, .prj, .cpg)
- shapefile/dicionario_colunas_shapefile.csv
- municipios_brasil.gpkg
"""

import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PASTA_SAIDA = Path(__file__).resolve().parent / "saida"
PASTA_SHAPEFILE = PASTA_SAIDA / "shapefile"
PASTA_SHAPEFILE.mkdir(parents=True, exist_ok=True)

ARQ_MALHA = RAIZ / "01_extracao_e_tratamento" / "saida" / "03_malha_ibge_dtb.gpkg"
ARQ_ICM_DESASTRES = PASTA_SAIDA / "01_icm_desastres.xlsx"
ARQ_SHP = PASTA_SHAPEFILE / "municipios_brasil.shp"
ARQ_DICIONARIO = PASTA_SHAPEFILE / "dicionario_colunas_shapefile.csv"
ARQ_GPKG = PASTA_SAIDA / "municipios_brasil.gpkg"

LIMITE_NOME_SHP = 10

# Nomes curtos (até 10 caracteres) usados no shapefile. Colunas que não estão
# aqui e passam de 10 caracteres são cortadas automaticamente (com número no
# final se o nome cortado repetir).
NOMES_SHAPEFILE = {
    # identificação e DTB
    "codigo_ibge": "cod_ibge",
    "municipiouf": "mun_uf",
    "cod_meso_regiao": "cod_meso",
    "meso_regiao": "meso_reg",
    "cod_regiao_geo_imediata": "cod_rgi",
    "regiao_geo_imediata": "rgi",
    "populacao_residente_2022": "pop_2022",
    "pop_estimada_dou_2026": "pop_2026",
    "densidade_hab_km2": "dens_km2",
    "domicilios_ocupados": "dom_ocup",
    "moradores_dom_ocupados": "mor_dom",
    "media_moradores_dom": "med_mor",
    "amazonia_legal": "amaz_legal",
    "municipio_costeiro": "costeiro",
    "bioma1_predominante": "bioma_1",
    "sub_regiao_sp": "sub_reg_sp",
    "regiao_turistica": "reg_tur",
    "categoria_turistica_sp": "cat_tur_sp",
    "categoria_sp": "cat_sp",
    # ICM e S2iD
    "faixa_populacional": "faixa_pop",
    "perfil_de_risco": "perfil_rsc",
    "dimensao_i": "dim_i",
    "dimensao_ii": "dim_ii",
    "dimensao_iii": "dim_iii",
    "classificacao_icm": "class_icm",
    "s2id_habilitado": "s2id_hab",
    # Atlas - danos humanos
    "cod_cobrade": "cobrade",
    "qtd_desastres": "qtd_desast",
    "dh_enfermos": "dh_enferm",
    "dh_desabrigados": "dh_desabr",
    "dh_desalojados": "dh_desaloj",
    "dh_desaparecidos": "dh_desapar",
    "dh_afetados_seca_estiagem": "dh_seca",
    "dh_total_danos_humanos_diretos": "dh_total",
    "dh_outros_afetados": "dh_outros",
    # Atlas - danos materiais (dan = danificadas, des = destruídas, vl = valor)
    "dm_uni_habita_danificadas": "dm_hab_dan",
    "dm_uni_habita_destruidas": "dm_hab_des",
    "dm_uni_habita_valor": "dm_hab_vl",
    "dm_inst_saude_danificadas": "dm_sau_dan",
    "dm_inst_saude_destruidas": "dm_sau_des",
    "dm_inst_saude_valor": "dm_sau_vl",
    "dm_inst_ensino_danificadas": "dm_ens_dan",
    "dm_inst_ensino_destruidas": "dm_ens_des",
    "dm_inst_ensino_valor": "dm_ens_vl",
    "dm_inst_servicos_danificadas": "dm_ser_dan",
    "dm_inst_servicos_destruidas": "dm_ser_des",
    "dm_inst_servicos_valor": "dm_ser_vl",
    "dm_inst_comuni_danificadas": "dm_com_dan",
    "dm_inst_comuni_destruidas": "dm_com_des",
    "dm_inst_comuni_valor": "dm_com_vl",
    "dm_obras_de_infra_danificadas": "dm_inf_dan",
    "dm_obras_de_infra_destruidas": "dm_inf_des",
    "dm_obras_de_infra_valor": "dm_inf_vl",
    "dm_total_danos_materiais": "dm_total",
    # Atlas - danos ambientais
    "da_polui_cont_da_agua": "da_agua",
    "da_polui_cont_do_ar": "da_ar",
    "da_polui_cont_do_solo": "da_solo",
    "da_dimi_exauri_hidrico": "da_hidrico",
    "da_incendi_parques_apas_apps": "da_incend",
    # Atlas - prejuízos econômicos públicos (R$)
    "pepl_assis_med_e_emergen_reais": "pepl_assis",
    "pepl_abast_de_agua_pot_reais": "pepl_agua",
    "pepl_sist_de_esgotos_sanit_reais": "pepl_esgot",
    "pepl_sis_limp_e_rec_lixo_reais": "pepl_lixo",
    "pepl_sis_cont_pragas_reais": "pepl_praga",
    "pepl_distrib_energia_reais": "pepl_energ",
    "pepl_telecomunicacoes_reais": "pepl_telec",
    "pepl_tran_loc_reg_l_curso_reais": "pepl_trans",
    "pepl_distrib_combustiveis_reais": "pepl_comb",
    "pepl_seguranca_publica_reais": "pepl_segur",
    "pepl_ensino_reais": "pepl_ensin",
    "pepl_total_publico": "pepl_total",
    # Atlas - prejuízos econômicos privados (R$)
    "pepr_agricultura_reais": "pepr_agric",
    "pepr_pecuaria_reais": "pepr_pecua",
    "pepr_industria_reais": "pepr_indus",
    "pepr_comercio_reais": "pepr_comer",
    "pepr_servicos_reais": "pepr_servi",
    "pepr_total_privado": "pepr_total",
    # controle
    "possui_registro_atlas": "reg_atlas",
}


def sanitizar_coluna(col):
    """snake_case sem acentos nem símbolos"""
    nfkd = unicodedata.normalize("NFKD", str(col))
    col_limpa = "".join([c for c in nfkd if not unicodedata.combining(c)])
    col_limpa = re.sub(r"[^a-zA-Z0-9_]", "_", col_limpa)
    col_limpa = re.sub(r"_+", "_", col_limpa)
    return col_limpa.strip("_").lower()


def nomes_curtos(colunas):
    """Nome do NOMES_SHAPEFILE ou, se não houver, o nome cortado em 10 caracteres sem repetir"""
    usados, mapa = set(), {}
    for col in colunas:
        curto = NOMES_SHAPEFILE.get(col, col)[:LIMITE_NOME_SHP]
        i = 1
        while curto in usados:
            sufixo = str(i)
            curto = col[:LIMITE_NOME_SHP - len(sufixo)] + sufixo
            i += 1
        usados.add(curto)
        mapa[col] = curto
    return mapa


# -----------------------------------------------------------------------------
# 1. Leitura
# -----------------------------------------------------------------------------
print("1/4 - Lendo malha (IBGE + DTB) e base ICM + Desastres...")
gdf_malha = gpd.read_file(ARQ_MALHA)
df_icm_desastres = pd.read_excel(ARQ_ICM_DESASTRES)

gdf_malha = gdf_malha.rename(columns={c: sanitizar_coluna(c) for c in gdf_malha.columns if c != "geometry"})

# Nome, UF e código da UF vêm da DTB (que cobre todos os polígonos da malha)
df_icm_desastres = df_icm_desastres.drop(columns=["municipio", "uf", "codigo_uf"])

# -----------------------------------------------------------------------------
# 2. Merge (a malha manda: um polígono por município)
# -----------------------------------------------------------------------------
print("2/4 - Cruzando pelo código IBGE...")
gdf_final = gdf_malha.merge(
    df_icm_desastres, on="codigo_ibge", how="left", validate="one_to_one", indicator=True
)

sem_dados = gdf_final.loc[gdf_final["_merge"] == "left_only", ["codigo_ibge", "municipio", "uf"]]
if len(sem_dados):
    print("  [aviso] municípios da malha sem ICM/Atlas (ficam com esses campos vazios):")
    print(sem_dados.to_string(index=False))

sem_poligono = sorted(set(df_icm_desastres["codigo_ibge"]) - set(gdf_malha["codigo_ibge"]))
if sem_poligono:
    print(f"  [aviso] municípios do ICM/Atlas sem polígono (ficam de fora): {sem_poligono}")

gdf_final = gdf_final.drop(columns=["_merge"])

colunas_iniciais = ["codigo_ibge", "municipio", "uf"]
outras = [c for c in gdf_final.columns if c not in colunas_iniciais + ["geometry"]]
gdf_final = gdf_final[colunas_iniciais + outras + ["geometry"]]

# Colunas só com números inteiros voltam a ser inteiras (o merge as transforma
# em decimal quando algum município fica sem dado, ex.: v1 = 1.0)
for col in outras:
    serie = gdf_final[col]
    if pd.api.types.is_float_dtype(serie) and (serie.dropna() % 1 == 0).all():
        gdf_final[col] = serie.astype("Int64")

# -----------------------------------------------------------------------------
# 3. GeoPackage (nomes completos)
# -----------------------------------------------------------------------------
print("3/4 - Gravando GeoPackage...")
gdf_final.to_file(ARQ_GPKG, driver="GPKG")

# -----------------------------------------------------------------------------
# 4. Shapefile (nomes de até 10 caracteres + dicionário)
# -----------------------------------------------------------------------------
print("4/4 - Gravando shapefile...")
mapa = nomes_curtos([c for c in gdf_final.columns if c != "geometry"])
gdf_shp = gdf_final.rename(columns=mapa)
gdf_shp.to_file(ARQ_SHP, driver="ESRI Shapefile", encoding="UTF-8")

pd.DataFrame(
    {"nome_shapefile": list(mapa.values()), "nome_completo": list(mapa.keys())}
).to_csv(ARQ_DICIONARIO, index=False, sep=";", encoding="utf-8-sig")

print("\n=======================================================")
print("BASE FINAL GERADA COM SUCESSO!")
print(f"Municípios (polígonos): {len(gdf_final)}")
print(f"Colunas de atributos:   {len(gdf_final.columns) - 1}")
print(f"Shapefile:  {ARQ_SHP}")
print(f"Dicionário: {ARQ_DICIONARIO}")
print(f"GeoPackage: {ARQ_GPKG}")
print("=======================================================")
