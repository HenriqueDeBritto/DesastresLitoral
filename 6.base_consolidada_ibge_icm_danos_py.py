# -*- coding: utf-8 -*-
"""
Script de Consolidação Final:
- Entrada 1: 5.Base_Mescla_IBGE_MUN.xlsx
- Entrada 2: 3.base_icm_danos.xlsx
- Saída: 6.base_consolidada_ibge_icm_danos.xlsx
"""

import os
import re
import unicodedata
import pandas as pd

# 1. Definir caminhos na pasta Downloads
pasta_downloads = r"C:\Users\Aluno\Downloads"
caminho_base5 = os.path.join(pasta_downloads, "5.Base_Mescla_IBGE_MUN.xlsx")
caminho_base3 = os.path.join(pasta_downloads, "3.base_icm_danos.xlsx")

print("1/4 - Lendo as duas bases...")
df5 = pd.read_excel(caminho_base5)
df3 = pd.read_excel(caminho_base3)

# 2. Padronização das chaves primárias
df5['codigo_ibge'] = df5['Codigo_Municipio_Unificado'].astype('Int64').astype(str).str.strip()
df3['codigo_ibge'] = df3['codigo_ibge'].astype('Int64').astype(str).str.strip()

# 3. Eliminar colunas redundantes e artefatos da Base 5 antes do merge
# Mantém 'municipio' e 'uf' da Base 3 para evitar nomes duplicados
colunas_remover_df5 = ['_merge', 'Codigo_Municipio_Unificado', 'Municipio', 'UF']
df5_clean = df5.drop(columns=[col for col in colunas_remover_df5 if col in df5.columns])

# 4. Realizar o JOIN (Left Join preservando a malha da base 5)
print("2/4 - Realizando cruzamento e eliminando duplicações...")
df_final = df5_clean.merge(df3, on='codigo_ibge', how='left')

# Preencher métricas numéricas com 0 para eventuais municípios sem desastres
colunas_metricas = [
    col for col in df3.columns 
    if col.startswith(('dh_', 'dm_', 'da_', 'pepl_', 'pepr_', 'pe_')) or col in ['v' + str(i) for i in range(1, 21)]
]
df_final[colunas_metricas] = df_final[colunas_metricas].fillna(0)

# 5. Higienização e sanitização dos nomes das colunas
print("3/4 - Sanitizando cabeçalhos...")
def sanitizar_coluna(col):
    nfkd = unicodedata.normalize('NFKD', str(col))
    col_limpa = "".join([c for c in nfkd if not unicodedata.combining(c)])
    col_limpa = col_limpa.replace('(R$)', '_reais').replace('(r$)', '_reais')
    col_limpa = col_limpa.replace("'", "").replace('"', '')
    col_limpa = re.sub(r'[^a-zA-Z0-9_]', '_', col_limpa)
    col_limpa = re.sub(r'_+', '_', col_limpa)
    return col_limpa.strip('_').lower()

df_final.columns = [sanitizar_coluna(col) for col in df_final.columns]

# Reorganizar: colocar codigo_ibge, municipio e uf logo no início da tabela
colunas_principais = ['codigo_ibge', 'municipio', 'uf']
outras_colunas = [c for c in df_final.columns if c not in colunas_principais]
df_final = df_final[colunas_principais + outras_colunas]

# 6. Salvar exclusivamente como arquivo Excel (.xlsx) começando com "6."
caminho_saida = os.path.join(pasta_downloads, "6.base_consolidada_ibge_icm_danos.xlsx")
print(f"4/4 - Gravando arquivo Excel final em: {caminho_saida} ...")
df_final.to_excel(caminho_saida, index=False)

print("\n=======================================================")
print("PROCESSAMENTO FINALIZADO COM SUCESSO!")
print(f"Total de Registros: {len(df_final)}")
print(f"Total de Colunas Consolidadas: {len(df_final.columns)}")
print(f"Arquivo gerado: {caminho_saida}")
print("=======================================================")