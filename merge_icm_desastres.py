import pandas as pd

caminho_icm = r"C:\Users\Aluno\Downloads\icm_tratado_v20260916.csv"
caminho_s2id = r"C:\Users\Aluno\Downloads\s2id_habilitados_v20260916.csv"
caminho_prioritarios = r"C:\Users\Aluno\Downloads\municipios_prioritarios_v20260916.csv"

# 1. Carrega os datasets tratados
df_icm = pd.read_csv(caminho_icm, sep=";", encoding="utf-8-sig")
df_s2id = pd.read_csv(caminho_s2id, sep=";", encoding="utf-8-sig")
df_prio = pd.read_csv(caminho_prioritarios, sep=";", encoding="utf-8-sig")

# 2. Padroniza a chave 'codigo_ibge' como inteira em todos os dataframes
df_icm["codigo_ibge"] = pd.to_numeric(df_icm["codigo_ibge"], errors="coerce").fillna(0).astype("int64")
df_s2id["codigo_ibge"] = pd.to_numeric(df_s2id["codigo_ibge"], errors="coerce").fillna(0).astype("int64")
df_prio["codigo_ibge"] = pd.to_numeric(df_prio["codigo_ibge"], errors="coerce").fillna(0).astype("int64")

# 3. Seleciona apenas as colunas necessárias para o enriquecimento
df_s2id_sub = df_s2id[["codigo_ibge", "s2id_habilitado"]].drop_duplicates(subset=["codigo_ibge"])
df_prio_sub = df_prio[["codigo_ibge", "municipio_prioritario"]].drop_duplicates(subset=["codigo_ibge"])

# 4. Faz o LEFT JOIN a partir da base do ICM
df_consolidado = df_icm.merge(df_s2id_sub, on="codigo_ibge", how="left")
df_consolidado = df_consolidado.merge(df_prio_sub, on="codigo_ibge", how="left")

# 5. Preenche municípios não encontrados com 0 (Não habilitado / Não prioritário)
df_consolidado["s2id_habilitado"] = df_consolidado["s2id_habilitado"].fillna(0).astype(int)
df_consolidado["municipio_prioritario"] = df_consolidado["municipio_prioritario"].fillna(0).astype(int)

# 6. Salva a base consolidada final
caminho_saida = r"C:\Users\Aluno\Downloads\icm_enriquecido_desastres_v20260916.csv"
df_consolidado.to_csv(caminho_saida, index=False, sep=";", encoding="utf-8-sig")

print("--- MERGE CONCLUÍDO COM SUCESSO! ---")
print(f"Total de municípios na base final: {len(df_consolidado)}")
print(f"Municípios com S2ID Habilitado: {df_consolidado['s2id_habilitado'].sum()}")
print(f"Municípios Prioritários em Gestão de Riscos: {df_consolidado['municipio_prioritario'].sum()}")
print("\nAmostra dos dados consolidados:")
print(df_consolidado[["codigo_ibge", "uf", "municipio", "categoria_grd", "s2id_habilitado", "municipio_prioritario"]].head())