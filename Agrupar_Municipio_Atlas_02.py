"""
Atlas de Desastres - agrupamento Município x Ano
O ano inicial é perguntado no console.

Regras (coluna "Agregação" do dicionário, linhas 2 a 71 do Excel):
    Drop = a coluna é descartada
    s    = a coluna é mantida (descritiva do município)
    Sum  = soma dos valores no ano
    Moda = valor mais frequente no ano
Resultado: UMA linha por município por ano.
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# 1) CONFIGURAÇÃO  (ajuste os caminhos para a sua máquina)
# ----------------------------------------------------------------------------
PASTA = Path(r"C:\Users\ana\OneDrive\Documentos\Ana Demarqui\Big Data")          # <<< ALTERE AQUI
ARQ_ATLAS = PASTA / "BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.xlsx"
ARQ_DICT = PASTA / "Data_Dictionary_meta_data.xlsx"
ABA_ATLAS = "Atlas Valores Originais"
ABA_DICT = "meta_data"
ARQ_SAIDA = PASTA / "Atlas_agrupado_municipio_ano.xlsx"

N_LINHAS_DICT = 70          # dicionário até a linha 71 do Excel (cabeçalho + 70)
COL_DATA_ANO = "Data_Evento"  # data usada para extrair o ANO (pode trocar por "Data_Registro")
COL_MUNICIPIO = "Cod_IBGE_Mun"  # chave do município (mais confiável que o nome)


def normaliza(txt):
    """minúsculo, sem acento, só letras/números (para comparar nomes)"""
    txt = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", txt.lower())


# ----------------------------------------------------------------------------
# 2) LEITURA
# ----------------------------------------------------------------------------
print("Lendo arquivos...")
df = pd.read_excel(ARQ_ATLAS, sheet_name=ABA_ATLAS)
dic = pd.read_excel(ARQ_DICT, sheet_name=ABA_DICT).iloc[:N_LINHAS_DICT].copy()

if len(dic) != df.shape[1]:
    raise ValueError(
        f"O dicionário tem {len(dic)} linhas e a tabela tem {df.shape[1]} colunas. "
        "Confira N_LINHAS_DICT."
    )

# Os nomes do dicionário estão normalizados (ex.: 'dm_inst_saude_valor') e os da
# tabela não (ex.: 'DM_Inst Saúde Valor'); por isso o vínculo é feito pela POSIÇÃO
# (mesma ordem nas duas planilhas). Abaixo, um aviso caso algo pareça desalinhado.
dic["coluna_atlas"] = df.columns.to_list()
dic["agregacao"] = dic["Agregação"].astype(str).str.strip().str.lower()

for _, r in dic.iterrows():
    a, b = normaliza(r["coluna_atlas"]), normaliza(r["nome_coluna"])
    if a[:6] != b[:6]:
        print(f"  [aviso] posição pode estar desalinhada: '{r['coluna_atlas']}' x '{r['nome_coluna']}'")

cols_sum = dic.loc[dic["agregacao"] == "sum", "coluna_atlas"].tolist()
cols_moda = dic.loc[dic["agregacao"] == "moda", "coluna_atlas"].tolist()
cols_manter = dic.loc[dic["agregacao"] == "s", "coluna_atlas"].tolist()
cols_drop = dic.loc[dic["agregacao"] == "drop", "coluna_atlas"].tolist()

print(f"Somar: {len(cols_sum)} | Moda: {len(cols_moda)} | Manter: {len(cols_manter)} | Descartar: {len(cols_drop)}")

# ----------------------------------------------------------------------------
# 3) ANO (criado ANTES do drop, pois a coluna de data é 'Drop' no dicionário)
# ----------------------------------------------------------------------------
df["Ano"] = pd.to_datetime(df[COL_DATA_ANO], errors="coerce").dt.year
df = df.dropna(subset=["Ano"]).copy()
df["Ano"] = df["Ano"].astype(int)

ano_min, ano_max = int(df["Ano"].min()), int(df["Ano"].max())

# ----------------------------------------------------------------------------
# 4) INPUT DO ANO INICIAL
# ----------------------------------------------------------------------------
while True:
    resp = input(f"A partir de qual ano deseja exibir? ({ano_min}-{ano_max}) [Enter = {ano_min}]: ").strip()
    if resp == "":
        ano_inicial = ano_min
        break
    if resp.isdigit() and ano_min <= int(resp) <= ano_max:
        ano_inicial = int(resp)
        break
    print(f"  Valor inválido. Digite um ano entre {ano_min} e {ano_max}.")

df = df[df["Ano"] >= ano_inicial].copy()
print(f"Filtrando de {ano_inicial} em diante: {len(df):,} registros de desastres.")

# ----------------------------------------------------------------------------
# 5) AGRUPAMENTO  (município + ano  ->  1 linha)
# ----------------------------------------------------------------------------
chaves = [COL_MUNICIPIO, "Ano"]

# 5.1 colunas mantidas ('s'): pega o primeiro valor do grupo
manter = [c for c in cols_manter if c != COL_MUNICIPIO]
agg = {c: "first" for c in manter}
# 5.2 colunas somadas
agg.update({c: "sum" for c in cols_sum})

res = df.groupby(chaves, as_index=False).agg(agg)


# 5.3 colunas de moda: valor mais frequente no município/ano (ignora vazios;
#     em caso de empate fica o menor valor / primeiro em ordem alfabética)
def moda_por_grupo(dados, coluna):
    cont = (
        dados.dropna(subset=[coluna])
        .groupby(chaves + [coluna])
        .size()
        .reset_index(name="_n")
        .sort_values(chaves + ["_n", coluna], ascending=[True, True, False, True])
        .drop_duplicates(chaves)
    )
    return cont[chaves + [coluna]]


for c in cols_moda:
    res = res.merge(moda_por_grupo(df, c), on=chaves, how="left")

# 5.4 quantidade de desastres agregados na linha (extra, útil para conferência)
qtd = df.groupby(chaves).size().reset_index(name="Qtd_Desastres")
res = res.merge(qtd, on=chaves, how="left")

# ----------------------------------------------------------------------------
# 6) ORGANIZA E SALVA
# ----------------------------------------------------------------------------
ordem = [COL_MUNICIPIO, "Ano"] + manter + ["Qtd_Desastres"] + cols_moda + cols_sum
res = res[ordem].sort_values(["Ano", COL_MUNICIPIO]).reset_index(drop=True)

print(f"Resultado: {res.shape[0]:,} linhas x {res.shape[1]} colunas")
res.to_excel(ARQ_SAIDA, index=False)
print(f"Arquivo salvo em: {ARQ_SAIDA}")