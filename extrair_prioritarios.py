import re
import pandas as pd
import pypdf

caminho_pdf = r"C:\Users\Aluno\Downloads\PUBL_relatorios_004_821_municipios_prioritarios.pdf"
caminho_saida = r"C:\Users\Aluno\Downloads\municipios_prioritarios_v20260916.csv"

leitor = pypdf.PdfReader(caminho_pdf)
dados_extraidos = []
padrao_municipio = re.compile(r"^\s*(\d+)\s+(.+?)\s+([A-Z]{2})\s+(\d{7})")

for pagina in leitor.pages:
  texto = pagina.extract_text()
  if not texto:
    continue
  for linha in texto.split("\n"):
    match = padrao_municipio.match(linha.strip())
    if match:
      seq, municipio, uf, cod_ibge = match.groups()
      dados_extraidos.append({
          "codigo_ibge": int(cod_ibge),
          "uf": uf.strip(),
          "municipio": municipio.strip(),
          "municipio_prioritario": 1,
      })

df_prioritarios = (
    pd.DataFrame(dados_extraidos)
    .drop_duplicates(subset=["codigo_ibge"])
    .reset_index(drop=True)
)
df_prioritarios.to_csv(
    caminho_saida, index=False, sep=";", encoding="utf-8-sig"
)
print(
    f"Base Municípios Prioritários exportada com sucesso: {len(df_prioritarios)}"
    " municípios!"
)