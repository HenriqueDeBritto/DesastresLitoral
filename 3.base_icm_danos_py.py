# -*- coding: utf-8 -*-
"""
Script Direto: Consolidação de 3.base_icm_danos.xlsx
Entradas:
- 2.base_merge_icm_desastres (ou 2.base_merge_icm_desastres_2)
- 1.sumariza_2013_em_diante
Saída:
- 3.base_icm_danos.xlsx
"""

import os
import glob
import re
import unicodedata
import pandas as pd

pasta_downloads = r"C:\Users\Aluno\Downloads"

# 1. Localizar e ler o arquivo de capacidades/ICM (2.base_merge_icm_desastres...)
candidatos_icm = [
    f for f in glob.glob(os.path.join(pasta_downloads, "*base_merge_icm_desastres*"))
    if not os.path.basename(f).startswith("~$")
]

if not candidatos_icm:
    raise FileNotFoundError(f"Nenhum arquivo 'base_merge_icm_desastres' encontrado em: {pasta_downloads}")

# Pega o arquivo mais recente (vai pegar o _2 se existir)
caminho_icm = sorted(candidatos_icm, key=os.path.getmtime, reverse=True)[0]
print(f"1/3 - Lendo base de capacidades: {os.path.basename(caminho_icm)}")

if caminho_icm.endswith('.csv'):
    df_icm = pd.read_csv(caminho_icm, sep=';', encoding='utf-8')
else:
    df_icm = pd.read_excel(caminho_icm)

# Filtrar apenas municípios válidos (remove anotações de rodapé com código 0)
df_icm = df_icm[pd.to_numeric(df_icm['codigo_ibge'], errors='coerce') > 0].copy()
df_icm['chave_ibge'] = df_icm['codigo_ibge'].astype(int).astype(str).str.strip()

# 2. Localizar e ler o arquivo de danos (1.sumariza_2013_em_diante...)
candidatos_danos = [
    f for f in glob.glob(os.path.join(pasta_downloads, "*sumariza_2013_em_diante*"))
    if not os.path.basename(f).startswith("~$")
]

if not candidatos_danos:
    raise FileNotFoundError(f"Arquivo 'sumariza_2013_em_diante' não encontrado em: {pasta_downloads}")

caminho_danos = candidatos_danos[0]
print(f"2/3 - Lendo base de danos: {os.path.basename(caminho_danos)}")
df_danos = pd.read_excel(caminho_danos)
df_danos['chave_ibge'] = df_danos['Cod_IBGE_Mun'].astype(int).astype(str).str.strip()

# Remover colunas repetidas do arquivo de danos antes do merge
colunas_duplicadas = ['Cod_IBGE_Mun', 'Nome_Municipio', 'Sigla_UF']
df_danos_clean = df_danos.drop(columns=[c for c in colunas_duplicadas if c in df_danos.columns])

# 3. Cruzamento das bases (Left Join para manter todos os 5.570 municípios)
print("3/3 - Fazendo o merge, padronizando colunas e salvando...")
df_final = df_icm.merge(df_danos_clean, on='chave_ibge', how='left')

# Preencher com 0 nas colunas numéricas de danos para municípios sem desastres registrados
colunas_metricas = [c for c in df_danos_clean.columns if c != 'chave_ibge']
df_final[colunas_metricas] = df_final[colunas_metricas].fillna(0)
df_final.drop(columns=['chave_ibge'], inplace=True)

# 4. Higienização completa dos nomes das colunas (snake_case, sem acentos nem símbolos)
def sanitizar_coluna(col):
    nfkd = unicodedata.normalize('NFKD', col)
    col_limpa = "".join([c for c in nfkd if not unicodedata.combining(c)])
    col_limpa = col_limpa.replace('(R$)', '_reais').replace('(r$)', '_reais')
    col_limpa = col_limpa.replace("'", "").replace('"', '')
    col_limpa = re.sub(r'[^a-zA-Z0-9_]', '_', col_limpa)
    col_limpa = re.sub(r'_+', '_', col_limpa)
    return col_limpa.strip('_').lower()

df_final.columns = [sanitizar_coluna(col) for col in df_final.columns]

# 5. Salvar exclusivamente como arquivo Excel (.xlsx)
caminho_saida = os.path.join(pasta_downloads, "3.base_icm_danos.xlsx")
df_final.to_excel(caminho_saida, index=False)

print("\n=======================================================")
print("ARQUIVO CRIADO COM SUCESSO!")
print(f"Total de Municípios: {len(df_final)}")
print(f"Total de Colunas Padronizadas: {len(df_final.columns)}")
print(f"Caminho do arquivo: {caminho_saida}")
print("=======================================================")