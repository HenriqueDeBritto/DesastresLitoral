# =====================================================================
# PREPARAÇÃO DO AMBIENTE 
# =====================================================================
import subprocess
import sys
import os

try:
    import pdfplumber
except ImportError:
    print("Instalando biblioteca pdfplumber para ler o PDF...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber", "--user"])
    import pdfplumber

import requests
import pandas as pd
import io


# =====================================================================
# PLANILHAS EXCEL - ICM
# =====================================================================
print("\n--- INICIANDO PROCESSAMENTO DO ICM (EXCEL) ---")

pasta_destino = r"C:\Users\ana\OneDrive\Documentos\Ana Demarqui\Big Data"
os.makedirs(pasta_destino, exist_ok=True)

arquivos = {
    "Faixa_A.xlsx": "https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/ICM_listaA_20260428.xlsx",
    "Faixa_B.xlsx": "https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/ICM_listaB_20260428.xlsx",
    "Faixa_C.xlsx": "https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/ICM_listaC_20260428.xlsx",
    "Faixa_D.xlsx": "https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/ICM_listaD_20260428.xlsx"
}

colunas = [
    "Código IBGE", "UF", "Código UF", "Município", "Faixa Populacional", "Região",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "Porte", "Perfil de Risco", "Dimensões I", "II", "III", "Total"
]

lista_df = []
headers_req = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

for nome_arquivo, url in arquivos.items():
    caminho = os.path.join(pasta_destino, nome_arquivo)
    print(f"Baixando {nome_arquivo}...")
    resp = requests.get(url, headers=headers_req)
    with open(caminho, "wb") as f:
        f.write(resp.content)
       
    df = pd.read_excel(caminho, skiprows=5, header=None, names=colunas)
    df["Código IBGE"] = pd.to_numeric(df["Código IBGE"], errors="coerce")
    df = df.dropna(subset=["Código IBGE"])
    df["Código IBGE"] = df["Código IBGE"].astype(int)
    lista_df.append(df)

df_unificado = pd.concat(lista_df, ignore_index=True)

for col in ["Dimensões I", "II", "III"]:
    df_unificado[col] = pd.to_numeric(df_unificado[col], errors='coerce').fillna(0)

df_unificado["Total"] = df_unificado["Dimensões I"] + df_unificado["II"] + df_unificado["III"]

def definir_classificacao(linha):
    perfil = str(linha["Perfil de Risco"]).lower()
    porte = str(linha["Porte"]).lower()
    dim1, dim2, dim3 = linha["Dimensões I"], linha["II"], linha["III"]
   
    if "prioritário" in perfil and "não" not in perfil:
        if dim1 >= 7 and dim2 >= 6 and dim3 >= 4: return "A"
        if dim1 >= 5 and dim2 >= 4 and dim3 >= 3: return "B"
        if dim1 >= 3 and dim2 >= 2 and dim3 >= 1: return "C"
        return "D"
    elif "médio" in porte or "grande" in porte:
        if dim1 >= 5 and dim2 >= 4 and dim3 >= 3: return "A"
        if dim1 >= 3 and dim2 >= 3 and dim3 >= 2: return "B"
        if dim1 >= 2 and dim2 >= 1 and dim3 >= 1: return "C"
        return "D"
    else:
        if dim1 >= 3 and dim2 >= 3 and dim3 >= 2: return "A"
        if dim1 >= 2 and dim2 >= 2 and dim3 >= 1: return "B"
        if dim1 >= 1 and dim2 >= 1 and dim3 >= 1: return "C"
        return "D"

df_unificado["Classificação"] = df_unificado.apply(definir_classificacao, axis=1)


# =====================================================================
# PDF S2iD
# =====================================================================
print("\n--- INICIANDO PROCESSAMENTO DO S2iD (PDF) ---")

url_pdf = "https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/sistema-integrado-de-informacoes-sobre-desastres/copy2_of_municipios_habilitados_s2iD_outubro_20211001.pdf"
print("Baixando o PDF do S2iD na memória...")
response_pdf = requests.get(url_pdf, headers=headers_req)

dados_tabela = []

print("Extraindo dados do PDF. Aguarde alguns segundos...")
with pdfplumber.open(io.BytesIO(response_pdf.content)) as pdf:
    for pagina in pdf.pages:
        tabela = pagina.extract_table()
        if tabela:
            dados_tabela.extend(tabela)

print("Montando o DataFrame do S2iD...")
df_s2id = pd.DataFrame(dados_tabela[1:], columns=dados_tabela[0])
df_s2id = df_s2id.replace('\n', ' ', regex=True)

coluna_1 = df_s2id.columns[0]
df_s2id = df_s2id[df_s2id[coluna_1] != coluna_1]


# =====================================================================
# CRUZAMENTO DAS TABELAS 
# =====================================================================
print("\n--- CRUZANDO OS DADOS (EXCEL + PDF) ---")

# Procura qual é a coluna do PDF que tem o nome dos municípios
col_mun_pdf = next((col for col in df_s2id.columns if 'munic' in str(col).lower()), df_s2id.columns[1])

# Padronização dos textos: Tudo maiúsculo, sem acentos e sem espaços sobrando nas pontas
muns_pdf_padronizado = df_s2id[col_mun_pdf].astype(str).str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.upper().str.strip()

muns_excel_padronizado = df_unificado['Município'].astype(str).str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8').str.upper().str.strip()


# Cria a nova coluna comparando se o município do Excel está dentro da lista do PDF
df_unificado['Habilitado_S2iD'] = muns_excel_padronizado.isin(muns_pdf_padronizado).map({True: 'Sim', False: 'Não'})


# Salva a planilha unificada e definitiva com a nova coluna
caminho_final = os.path.join(pasta_destino, "ICM_Unificado_Final.xlsx")
df_unificado.to_excel(caminho_final, index=False)

print(f"\nCruzamento concluído com sucesso!")
print(f"Planilha final salva com a coluna 'Habilitado_S2iD' em: {caminho_final}")
print("\nPrévia do resultado:")
print(df_unificado[['Município', 'UF', 'Classificação', 'Habilitado_S2iD']].head(10))