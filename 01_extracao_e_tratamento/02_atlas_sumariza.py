# -*- coding: utf-8 -*-
"""
ETAPA 02 - Atlas de Desastres: sumarização por município

Agrupa os registros do Atlas Digital de Desastres em UMA linha por município,
considerando os desastres a partir de ANO_INICIAL.

Regras (coluna "Agregação" do dicionário, linhas 2 a 71 da aba meta_data):
    Drop = a coluna é descartada
    s    = a coluna é mantida (descritiva do município)
    Sum  = soma dos valores no período
    Moda = valor mais frequente no período

Entradas (dados/entrada/):
- BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.xlsx   (Atlas bruto - opcional)
- dicionario_de_dados.xlsx
- atlas_sumariza_2013_em_diante.xlsx   (base já sumarizada, usada se o Atlas bruto não estiver na pasta)
Saída:
- 01_extracao_e_tratamento/saida/02_atlas_sumariza.xlsx
"""

import re
import shutil
import unicodedata
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# 1) CONFIGURAÇÃO
# ----------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
PASTA_ENTRADA = RAIZ / "dados" / "entrada"
PASTA_SAIDA = Path(__file__).resolve().parent / "saida"
PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

ARQ_ATLAS = PASTA_ENTRADA / "BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.xlsx"
ARQ_DICT = PASTA_ENTRADA / "dicionario_de_dados.xlsx"
ARQ_BASE_PRONTA = PASTA_ENTRADA / "atlas_sumariza_2013_em_diante.xlsx"
ARQ_SAIDA = PASTA_SAIDA / "02_atlas_sumariza.xlsx"

ABA_ATLAS = "Atlas Valores Originais"
ABA_DICT = "meta_data"

ANO_INICIAL = 2013              # desastres a partir deste ano
AGRUPAR_POR_ANO = False         # True = uma linha por município POR ANO
N_LINHAS_DICT = 70              # dicionário até a linha 71 do Excel (cabeçalho + 70)
COL_DATA_ANO = "Data_Evento"    # data usada para extrair o ANO (pode trocar por "Data_Registro")
COL_MUNICIPIO = "Cod_IBGE_Mun"  # chave do município (mais confiável que o nome)


# ----------------------------------------------------------------------------
# 2) SEM O ATLAS BRUTO: usa a base já sumarizada
# ----------------------------------------------------------------------------
if not ARQ_ATLAS.exists():
    print(f"Atlas bruto não encontrado em: {ARQ_ATLAS}")
    print(f"Usando a base já sumarizada: {ARQ_BASE_PRONTA.name}")
    shutil.copyfile(ARQ_BASE_PRONTA, ARQ_SAIDA)
    print(f"Arquivo salvo em: {ARQ_SAIDA}")
    raise SystemExit(0)


def normaliza(txt):
    """minúsculo, sem acento, só letras/números (para comparar nomes)"""
    txt = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", txt.lower())


# ----------------------------------------------------------------------------
# 3) LEITURA
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
# 4) ANO (criado ANTES do drop, pois a coluna de data é 'Drop' no dicionário)
# ----------------------------------------------------------------------------
df["Ano"] = pd.to_datetime(df[COL_DATA_ANO], errors="coerce", dayfirst=True).dt.year
df = df.dropna(subset=["Ano"]).copy()
df["Ano"] = df["Ano"].astype(int)

df = df[df["Ano"] >= ANO_INICIAL].copy()
print(f"Filtrando de {ANO_INICIAL} em diante: {len(df):,} registros de desastres.")

# ----------------------------------------------------------------------------
# 5) AGRUPAMENTO  (município [+ ano]  ->  1 linha)
# ----------------------------------------------------------------------------
chaves = [COL_MUNICIPIO, "Ano"] if AGRUPAR_POR_ANO else [COL_MUNICIPIO]

# 5.1 colunas mantidas ('s'): pega o primeiro valor do grupo
manter = [c for c in cols_manter if c != COL_MUNICIPIO]
agg = {c: "first" for c in manter}
# 5.2 colunas somadas
agg.update({c: "sum" for c in cols_sum})

res = df.groupby(chaves, as_index=False).agg(agg)


# 5.3 colunas de moda: valor mais frequente no grupo (ignora vazios;
#     em caso de empate fica o menor valor / primeiro em ordem alfabética)
def moda_por_grupo(dados, coluna):
    cont = (
        dados.dropna(subset=[coluna])
        .groupby(chaves + [coluna])
        .size()
        .reset_index(name="_n")
        .sort_values(chaves + ["_n", coluna], ascending=[True] * len(chaves) + [False, True])
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
ordem = chaves + manter + ["Qtd_Desastres"] + cols_moda + cols_sum
res = res[ordem].sort_values(chaves[::-1]).reset_index(drop=True)

print(f"Resultado: {res.shape[0]:,} linhas x {res.shape[1]} colunas")
res.to_excel(ARQ_SAIDA, index=False)
print(f"Arquivo salvo em: {ARQ_SAIDA}")
