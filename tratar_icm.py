import pandas as pd

# Caminho de entrada e saída
caminho_entrada = r"C:\Users\Aluno\Downloads\base_completa_icm_082026.xlsx"
caminho_saida = r"C:\Users\Aluno\Downloads\icm_tratado_v20260916.csv"

# 1. Carrega ignorando o título da Linha 0
df = pd.read_excel(caminho_entrada, header=1)

# 2. Renomeia 1 a 20 para v1 a v20
mapa_renomear = {}
for i in range(1, 21):
    for chave in [i, float(i), str(i), f"{i}.0"]:
        mapa_renomear[chave] = f"v{i}"

df = df.rename(columns=mapa_renomear)

# 3. Converte v1 a v20 para inteiros booleanos (0 ou 1)
colunas_v = [f"v{i}" for i in range(1, 21)]
for col in colunas_v:
    if col in df.columns:
        df[col] = df[col].fillna(0).astype(int)

# 4. Consolida a coluna categoria_grd a partir das colunas AA até AL
colunas_aa_al = df.columns[26:]


def consolidar_grd(linha):
  for col in colunas_aa_al:
    val = str(linha[col]).strip().upper()
    if val in ["A", "B", "C", "D"]:
      return val
  return None


df["categoria_grd"] = df.apply(consolidar_grd, axis=1)

# 5. Seleciona as colunas padronizadas
colunas_ordem = [
    "Código IBGE",
    "UF",
    "Município",
    "Região",
] + colunas_v + ["Soma", "categoria_grd"]
df_final = df[[c for c in colunas_ordem if c in df.columns]].copy()

# 6. Converte nomes de colunas para snake_case
df_final.columns = (
    df_final.columns.astype(str)
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("ó", "o")
    .str.replace("í", "i")
    .str.replace("ã", "a")
)

# 7. Salva a base tratada
df_final.to_csv(caminho_saida, index=False, sep=";", encoding="utf-8-sig")
print("Base ICM tratada e exportada com sucesso!")