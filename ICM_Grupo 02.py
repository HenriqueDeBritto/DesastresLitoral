# PowerShell
# pip install pandas openpyxl requests

import os
import requests
import pandas as pd

# Configurar a pasta e os links
pasta_destino = r"C:\Users\Aluno\Documents\Ana Demarqui\ICM"
os.makedirs(pasta_destino, exist_ok=True)

arquivos = {
    "Faixa_A.xlsx": "https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/ICM_listaA_20260428.xlsx",
    "Faixa_B.xlsx": "https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/ICM_listaB_20260428.xlsx",
    "Faixa_C.xlsx": "https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/ICM_listaC_20260428.xlsx",
    "Faixa_D.xlsx": "https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/ICM_listaD_20260428.xlsx"
}

# Cabeçalho das colunas
colunas = [
    "Código IBGE", "UF", "Código UF", "Município", "Faixa Populacional", "Região",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", 
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "Porte", "Perfil de Risco", "Dimensões I", "II", "III", "Total"
]

lista_df = []
headers_req = {"User-Agent": "Mozilla/5.0"}

print("Iniciando o download e processamento das planilhas...")

# Baixar e ler os 4 arquivos
for nome_arquivo, url in arquivos.items():
    caminho = os.path.join(pasta_destino, nome_arquivo)
    
    print(f"Baixando {nome_arquivo}...")
    resp = requests.get(url, headers=headers_req)
    with open(caminho, "wb") as f:
        f.write(resp.content)
        
    #skip rows define o numero de linhas para ignorar, + considerando somente as colunas informadas
    df = pd.read_excel(caminho, skiprows=5, header=None, names=colunas)
    
    # --- LIMPEZA GARANTIDA DOS MUNICÍPIOS ---
    # Transforma a coluna IBGE em número. Se for um texto de rodapé, vira 'NaN' (nulo)
    df["Código IBGE"] = pd.to_numeric(df["Código IBGE"], errors="coerce")
    
    # Apaga todas as linhas onde o IBGE ficou nulo (ou seja, tudo que não era município)
    df = df.dropna(subset=["Código IBGE"])
    
    # Volta o código IBGE para número inteiro para não ficar com casas decimais (ex: 3550308.0)
    df["Código IBGE"] = df["Código IBGE"].astype(int)
    # --------------------------------------------------
    
    lista_df.append(df)

# Unificar todas as tabelas
print("Unificando os municípios...")
df_unificado = pd.concat(lista_df, ignore_index=True)

# Garantir que as colunas de dimensão sejam números
for col in ["Dimensões I", "II", "III"]:
    df_unificado[col] = pd.to_numeric(df_unificado[col], errors='coerce').fillna(0)

# Calcular o Total
df_unificado["Total"] = df_unificado["Dimensões I"] + df_unificado["II"] + df_unificado["III"]

# CRIAR A LÓGICA DE CLASSIFICAÇÃO BASEADA NA TABELA
def definir_classificacao(linha):
    # Pegamos os dados da linha convertidos para minúsculo para evitar erro de digitação da planilha
    perfil = str(linha["Perfil de Risco"]).lower()
    porte = str(linha["Porte"]).lower()
    dim1 = linha["Dimensões I"]
    dim2 = linha["II"]
    dim3 = linha["III"]
    
    # Regra 1: Municípios Prioritários
    if "prioritário" in perfil and "não" not in perfil:
        if dim1 >= 7 and dim2 >= 6 and dim3 >= 4: return "A"
        if dim1 >= 5 and dim2 >= 4 and dim3 >= 3: return "B"
        if dim1 >= 3 and dim2 >= 2 and dim3 >= 1: return "C"
        return "D"
        
    # Regra 2: Municípios Não Prioritários de Médio e Grande Porte
    elif "médio" in porte or "grande" in porte:
        if dim1 >= 5 and dim2 >= 4 and dim3 >= 3: return "A"
        if dim1 >= 3 and dim2 >= 3 and dim3 >= 2: return "B"
        if dim1 >= 2 and dim2 >= 1 and dim3 >= 1: return "C"
        return "D"
        
    # Regra 3: Municípios Não Prioritários de Pequeno Porte
    else:
        if dim1 >= 3 and dim2 >= 3 and dim3 >= 2: return "A"
        if dim1 >= 2 and dim2 >= 2 and dim3 >= 1: return "B"
        if dim1 >= 1 and dim2 >= 1 and dim3 >= 1: return "C"
        return "D"

# Aplicar a regra para criar a coluna extra
df_unificado["Classificação"] = df_unificado.apply(definir_classificacao, axis=1)

# Salvar o arquivo final unificado
caminho_final = os.path.join(pasta_destino, "ICM_Unificado_Todos_Municipios.xlsx")
df_unificado.to_excel(caminho_final, index=False)

print(f"\nPronto! O arquivo unificado contém {len(df_unificado)} municípios e já possui a coluna de Classificação.")
print(f"Salvo em: {caminho_final}")



# =====================================================================
