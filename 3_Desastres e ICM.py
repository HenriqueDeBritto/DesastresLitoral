# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 19:44:47 2026

@author: ANA E CAIQUE
"""
import pandas as pd
import os

print("📥 1. Lendo os arquivos Excel...")

# Caminhos dos arquivos
pasta = r"C:\Users\Aluno\Documents\Ana Demarqui\07102026"
arquivo_sumariza = os.path.join(pasta, "1.sumariza_2013_em_diante.xlsx")
arquivo_icm = os.path.join(pasta, "2.base_merge_icm_desastres.xlsx")

# Lendo os arquivos
df_sumariza = pd.read_excel(arquivo_sumariza)
df_icm = pd.read_excel(arquivo_icm)

# Limpeza opcional de "linhas fantasmas" vazias nos arquivos originais
df_sumariza = df_sumariza.dropna(subset=['Cod_IBGE_Mun'])
df_icm = df_icm.dropna(subset=['Código IBGE'])

print("✅ Arquivos carregados com sucesso!")

# -----------------------------------------------------------------------------
# 2. Tratamento das chaves de cruzamento (Código IBGE)
# -----------------------------------------------------------------------------
df_sumariza['Cod_IBGE_Mun'] = pd.to_numeric(df_sumariza['Cod_IBGE_Mun'], errors='coerce').astype('Int64').astype(str)
df_icm['Código IBGE'] = pd.to_numeric(df_icm['Código IBGE'], errors='coerce').astype('Int64').astype(str)

# -----------------------------------------------------------------------------
# 3. Mesclando as tabelas (Merge)
# -----------------------------------------------------------------------------
print("🔄 2. Realizando o cruzamento das tabelas (Full Outer Join)...")

df_mesclado = pd.merge(
    df_sumariza, 
    df_icm, 
    left_on='Cod_IBGE_Mun', 
    right_on='Código IBGE', 
    how='outer',
    indicator=True
)

# -----------------------------------------------------------------------------
# 4. Unificando as colunas antes de apagar (O TRUQUE PARA NÃO PERDER DADOS)
# -----------------------------------------------------------------------------
# Se Nome_Municipio estiver vazio (porque a cidade só estava na tabela 2), ele pega da coluna Município
df_mesclado['Nome_Municipio'] = df_mesclado['Nome_Municipio'].combine_first(df_mesclado['Município'])

# Se a UF estiver vazia, pega da Sigla_UF
if 'UF' in df_mesclado.columns and 'Sigla_UF' in df_mesclado.columns:
    df_mesclado['UF'] = df_mesclado['UF'].combine_first(df_mesclado['Sigla_UF'])

# Se o código IBGE principal ficou vazio, garante que ele puxe do código da direita
df_mesclado['Cod_IBGE_Mun'] = df_mesclado['Cod_IBGE_Mun'].combine_first(df_mesclado['Código IBGE'])

# -----------------------------------------------------------------------------
# 5. Limpeza de Colunas Repetidas
# -----------------------------------------------------------------------------
colunas_para_dropar = ['Código IBGE', 'Sigla_UF', 'Código UF', 'Município']

colunas_existentes = [col for col in colunas_para_dropar if col in df_mesclado.columns]
df_final = df_mesclado.drop(columns=colunas_existentes)

print(f"🗑️ Colunas removidas para limpeza: {colunas_existentes}")

# -----------------------------------------------------------------------------
# 6. Reordenando as colunas (Organização visual)
# -----------------------------------------------------------------------------
# Puxa UF e Região para o começo da tabela, logo após o Nome do Município e Código IBGE
colunas_iniciais = ['Nome_Municipio', 'Cod_IBGE_Mun', 'UF', 'Região']

# Filtra as colunas que realmente existem para evitar erros
colunas_iniciais = [c for c in colunas_iniciais if c in df_final.columns]
outras_colunas = [c for c in df_final.columns if c not in colunas_iniciais and c != '_merge']

# Junta as colunas ordenadas
df_final = df_final[colunas_iniciais + outras_colunas]

# -----------------------------------------------------------------------------
# 7. Salvar o arquivo final
# -----------------------------------------------------------------------------
caminho_final = os.path.join(pasta, "3.Merge_Final_Desastres_ICM.xlsx")
print("\n💾 3. Salvando a tabela final em Excel...")

# Salva o arquivo final removendo a coluna '_merge' para ficar limpo
df_final.drop(columns=['_merge'], errors='ignore').to_excel(caminho_final, index=False)

print(f"✨ Sucesso! O arquivo final completo e unificado foi gerado em:\n{caminho_final}")