# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 21:16:39 2026

@author: ANA E CAIQUE
"""
import pandas as pd
import os

print("📥 1. Lendo os arquivos Excel...")

# Caminhos dos arquivos (ajuste a pasta se necessário)
pasta = r"C:\Users\Aluno\Documents\Ana Demarqui\07102026"
arquivo_icm_desastres = os.path.join(pasta, "3.Merge_Desastres_ICM.xlsx")
arquivo_ibge = os.path.join(pasta, "Base 05_Mescla_IBGE_MUN.xlsx")

# Lendo os arquivos
df_desastres = pd.read_excel(arquivo_icm_desastres)
df_ibge = pd.read_excel(arquivo_ibge)

# Remover a coluna '_merge' antiga que ficou no arquivo da Base 05
if '_merge' in df_ibge.columns:
    df_ibge = df_ibge.drop(columns=['_merge'])

print("✅ Arquivos carregados com sucesso!")

# -----------------------------------------------------------------------------
# 2. Tratamento das chaves de cruzamento (Código IBGE)
# -----------------------------------------------------------------------------
df_desastres['Cod_IBGE_Mun'] = pd.to_numeric(df_desastres['Cod_IBGE_Mun'], errors='coerce').astype('Int64').astype(str)
df_ibge['Codigo_Municipio_Unificado'] = pd.to_numeric(df_ibge['Codigo_Municipio_Unificado'], errors='coerce').astype('Int64').astype(str)

# Limpeza de linhas vazias (Fantasmas)
df_desastres = df_desastres.dropna(subset=['Cod_IBGE_Mun'])
df_ibge = df_ibge.dropna(subset=['Codigo_Municipio_Unificado'])

# -----------------------------------------------------------------------------
# 3. Mesclando as tabelas (Merge)
# -----------------------------------------------------------------------------
print("🔄 2. Realizando o cruzamento das tabelas (Full Outer Join)...")

df_mesclado = pd.merge(
    df_desastres, 
    df_ibge, 
    left_on='Cod_IBGE_Mun', 
    right_on='Codigo_Municipio_Unificado', 
    how='outer',
    suffixes=('', '_ibge'), 
    indicator=True
)

# -----------------------------------------------------------------------------
# 4. Unificando as colunas antes de apagar
# -----------------------------------------------------------------------------
df_mesclado['Cod_IBGE_Mun'] = df_mesclado['Cod_IBGE_Mun'].combine_first(df_mesclado['Codigo_Municipio_Unificado'])

if 'Municipio' in df_mesclado.columns:
    df_mesclado['Nome_Municipio'] = df_mesclado['Nome_Municipio'].combine_first(df_mesclado['Municipio'])

if 'UF_ibge' in df_mesclado.columns:
    df_mesclado['UF'] = df_mesclado['UF'].combine_first(df_mesclado['UF_ibge'])

# -----------------------------------------------------------------------------
# 5. Limpeza de Colunas Repetidas e Desnecessárias
# -----------------------------------------------------------------------------
colunas_para_dropar = ['Codigo_Municipio_Unificado', 'Municipio', 'UF_ibge']

colunas_existentes = [col for col in colunas_para_dropar if col in df_mesclado.columns]
df_final = df_mesclado.drop(columns=colunas_existentes)

print(f"🗑️ Colunas removidas para limpeza: {colunas_existentes}")

# -----------------------------------------------------------------------------
# 6. Reordenando as colunas principais (Organização visual)
# -----------------------------------------------------------------------------
colunas_iniciais = ['Nome_Municipio', 'Cod_IBGE_Mun', 'Cod_SIAFI', 'UF', 'Região', 'nome_UF', 'geometry']

colunas_iniciais = [c for c in colunas_iniciais if c in df_final.columns]
outras_colunas = [c for c in df_final.columns if c not in colunas_iniciais and c != '_merge']

df_final = df_final[colunas_iniciais + outras_colunas]

# -----------------------------------------------------------------------------
# 7. Salvar o arquivo final
# -----------------------------------------------------------------------------
# Remove a coluna '_merge' do contador e do arquivo final, se existir
if '_merge' in df_final.columns:
    df_final = df_final.drop(columns=['_merge'])

# ---- NOVO: Exibir quantidade total de colunas ----
total_colunas = len(df_final.columns)
print(f"\n📊 Total de colunas na base final: {total_colunas}")
# --------------------------------------------------

caminho_final = os.path.join(pasta, "6.Base_Consolidada_Final.xlsx")
print("💾 3. Salvando a tabela final em Excel...")

if 'geometry' in df_final.columns:
    df_final['geometry'] = df_final['geometry'].astype(str)

df_final.to_excel(caminho_final, index=False)

print(f"✨ Sucesso! A grande Base Consolidada foi gerada em:\n{caminho_final}")