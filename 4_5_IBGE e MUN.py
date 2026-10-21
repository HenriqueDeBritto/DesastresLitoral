# -*- coding: utf-8 -*-
"""
Created on Wed Sep 30 21:14:43 2026

@author: ANA E CAIQUE
"""

import geobr
import matplotlib.pyplot as plt
import pandas as pd
import os

print("📥 Baixando mapa dos municípios do IBGE via geobr...")
print("⚠️ (Por ser o Brasil inteiro, pode levar de 30 a 60 segundos na primeira vez)")

# 1. Baixar a malha de todos os municípios do Brasil (Ano 2022)
municipios = geobr.read_municipality(code_muni="all", year=2022)

# 2. Garantir que o código do município seja string (texto) sem casas decimais (.0)
municipios['code_muni'] = municipios['code_muni'].astype('Int64').astype(str)

print("✅ Download concluído com sucesso!")
print(f"📊 Total de municípios carregados: {len(municipios)}")
print("\n🔍 Primeiras linhas da base de dados:")
print(municipios[['code_muni', 'name_muni', 'abbrev_state']].head())

# 3. Exibir o mapa no painel 'Plots' do Spyder
print("\n🗺️ Gerando visualização do mapa no painel do Spyder...")
plt.figure(figsize=(10, 10)) 
municipios.plot(color='white', edgecolor='black', linewidth=0.1)
plt.title("Municípios do Brasil - IBGE", fontsize=14)
plt.axis("off")
plt.tight_layout()
plt.show()

# 4. Salvar o resultado em uma tabela Excel
# Configurando a pasta onde o arquivo será salvo
pasta_destino = r"C:\Users\Aluno\Documents\Ana Demarqui\30092026"
os.makedirs(pasta_destino, exist_ok=True)
caminho_tabela = os.path.join(pasta_destino, "Tabela_Municipios_IBGE.xlsx")

print("\n💾 Salvando os dados em uma tabela Excel...")

# O formato shapefile possui uma coluna com os polígonos do mapa chamada "geom".
# Como o Excel não suporta desenhos geométricos nas células, nós removemos essa 
# coluna específica apenas para salvar a tabela limpa.
nome_coluna_geometria = municipios.active_geometry_name
df_tabela = pd.DataFrame(municipios.drop(columns=[nome_coluna_geometria]))

# Salva o arquivo final
df_tabela.to_excel(caminho_tabela, index=False)

print(f"✨ Sucesso! Tabela gerada e salva em:\n{caminho_tabela}")




# ----------------------------------------   SEGUNDA PARTE
# DataFrame gerado do IBGE  + DTB_Brasil_Municipios_biomas.siafi.censo
# ----------------------------------------   
# SEGUNDA PARTE

print("\n📥 Iniciando a Segunda Parte: Cruzamento de Dados e Tratamentos...")

# 1. Filtra as colunas do IBGE (mantendo apenas o código e a geometria)
col_geometria = municipios.active_geometry_name
municipios_reduzido = municipios[['code_muni', col_geometria]]

# 2. Ler o arquivo Excel
caminho_excel = os.path.join(pasta_destino, "DTB_Brasil_Municipios_biomas.siafi.censo.xlsx")
print(f"📖 Lendo o arquivo Excel:\n{caminho_excel}")
df_excel = pd.read_excel(caminho_excel)

# =============================================================================
# NOMES DAS COLUNAS (Altere se estiverem escritos diferente no seu arquivo)
COLUNA_CODIGO_EXCEL = 'Cod_Mun'
COLUNA_SIAFI = 'codigo siaf' 
# =============================================================================

# 3. Trata os códigos do Excel (Garante que sejam String sem casas decimais)
df_excel[COLUNA_CODIGO_EXCEL] = pd.to_numeric(
    df_excel[COLUNA_CODIGO_EXCEL], errors='coerce'
).astype('Int64').astype(str)

# Trata a coluna SIAFI (Se ela existir no arquivo, converte para texto)
if COLUNA_SIAFI in df_excel.columns:
    df_excel[COLUNA_SIAFI] = pd.to_numeric(
        df_excel[COLUNA_SIAFI], errors='coerce'
    ).astype('Int64').astype(str)
else:
    print(f"⚠️ Aviso: A coluna '{COLUNA_SIAFI}' não foi encontrada. Verifique o nome.")

# 4. Cruzamento Full Outer Join
print("🔄 Juntando as tabelas...")
df_final = pd.merge(
    municipios_reduzido,
    df_excel,
    left_on='code_muni',
    right_on=COLUNA_CODIGO_EXCEL,
    how='outer',
    indicator=True
)

# 5. Tratamento das colunas duplicadas
# Cria uma coluna única pegando o código do IBGE. Se for vazio, pega o código do Excel.
df_final['Codigo_Municipio_Unificado'] = df_final['code_muni'].combine_first(df_final[COLUNA_CODIGO_EXCEL])

# Exclui as colunas antigas para não ficar duplicado
df_final = df_final.drop(columns=['code_muni', COLUNA_CODIGO_EXCEL])

# Organiza a coluna unificada para ser a primeira da tabela
colunas = ['Codigo_Municipio_Unificado'] + [col for col in df_final.columns if col != 'Codigo_Municipio_Unificado']
df_final = df_final[colunas]

# 6. Salvar o arquivo final com a geometria
# O Excel não suporta objetos geométricos (polígonos), então transformamos a geometria em texto (String)
df_final[col_geometria] = df_final[col_geometria].astype(str)

caminho_final = os.path.join(pasta_destino, "5.Base_Mescla_IBGE_MUN.xlsx")
print("\n💾 Salvando a tabela final mesclada em Excel...")
df_final.to_excel(caminho_final, index=False)

# 7. Exibe o resultado final
print(f"✨ Sucesso! Arquivo final gerado em:\n{caminho_final}")
print("\n📊 RESULTADO DO CRUZAMENTO (Coluna '_merge'):")
print(df_final['_merge'].value_counts())