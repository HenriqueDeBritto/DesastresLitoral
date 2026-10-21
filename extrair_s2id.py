import re
import pandas as pd
import pypdf

caminho_pdf = r"C:\Users\Aluno\Downloads\copy2_of_municipios_habilitados_s2iD_outubro_20211001.pdf"
caminho_saida = r"C:\Users\Aluno\Downloads\s2id_habilitados_v20260916.csv"

leitor = pypdf.PdfReader(caminho_pdf)
dados_extraidos = []
padrao_linha = re.compile(r"^\s*(\d+)\s+(.+?)\s+(\d{7})\s+(.+?)\s+([A-Z]{2})\s*$")

for pagina in leitor.pages:
  texto = pagina.extract_text()
  if not texto:
    continue
  for linha in texto.split("\n"):
    match = padrao_linha.match(linha.strip())
    if match:
      seq, municipio, cod_ibge, regiao_estado, uf = match.groups()
      partes = regiao_estado.split()
      regiao = partes[0] if partes else ""
      estado = " ".join(partes[1:]) if len(partes) > 1 else ""
      dados_extraidos.append({
          "codigo_ibge": int(cod_ibge),
          "uf": uf.strip(),
          "municipio": municipio.strip(),
          "regiao": regiao.strip(),
          "estado": estado.strip(),
          "s2id_habilitado": 1,
      })

df_s2id = (
    pd.DataFrame(dados_extraidos)
    .drop_duplicates(subset=["codigo_ibge"])
    .reset_index(drop=True)
)
df_s2id.to_csv(caminho_saida, index=False, sep=";", encoding="utf-8-sig")
print(
    f"Base S2ID finalizada com sucesso: {len(df_s2id)} municípios habilitados!"
)