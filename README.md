# Desastres naturais nos municípios — TCC

Scripts do trabalho de conclusão de curso sobre desastres naturais nos municípios
da RMVale (Região Metropolitana do Vale do Paraíba e Litoral Norte).

O pipeline monta **uma base única, em shapefile, com todos os municípios do
Brasil** (polígonos oficiais do IBGE + indicadores da DTB + ICM + S2iD + danos do
Atlas de Desastres) e depois recorta os **39 municípios da RMVale**.

## Como rodar

```bash
pip install -r requirements.txt
python executar_pipeline.py
```

Cada script também pode ser rodado sozinho, na ordem abaixo. Os caminhos são
relativos à pasta do projeto, então funcionam em qualquer computador.

## Estrutura

```
dados/
  entrada/                        bases que não são baixadas por script (versionadas)
    atlas_sumariza_2013_em_diante.xlsx
    dtb_municipios_biomas_siafi_censo.xlsx
    dicionario_de_dados.xlsx
  downloads/                      baixados pelos scripts (fora do Git)
01_extracao_e_tratamento/
  01_icm_s2id.py                  ICM (faixas A-D) + municípios habilitados no S2iD
  02_atlas_sumariza.py            danos do Atlas, uma linha por município (2013+)
  03_ibge_malha_dtb.py            shapefile do IBGE 2025 + DTB
  saida/                          (fora do Git)
02_consolidacao_e_merge/
  01_merge_icm_desastres.py       ICM + Atlas
  02_merge_shapefile_final.py     malha + tudo  ->  shapefile final
  saida/                          (fora do Git)
    shapefile/municipios_brasil.shp
    shapefile/dicionario_colunas_shapefile.csv
    municipios_brasil.gpkg
03_Filtragem_RM_Vale/
  01_filtrar_rmvale.py            recorte dos 39 municípios da RMVale
  saida/                          (fora do Git)
    shapefile/municipios_rmvale.shp
    shapefile/dicionario_colunas_shapefile.csv
    municipios_rmvale.gpkg
    municipios_rmvale.xlsx        mesma tabela, sem polígonos
```

## Fluxo dos dados

| Etapa | Entrada | Saída |
|---|---|---|
| 01.01 | ICM listas A-D (gov.br/mdr, baixado) · PDF S2iD out/2021 (baixado) | `01_icm_s2id.xlsx` |
| 01.02 | Atlas bruto (se existir em `dados/entrada`) ou `atlas_sumariza_2013_em_diante.xlsx` | `02_atlas_sumariza.xlsx` |
| 01.03 | Malha Municipal IBGE 2025 (baixada) · DTB | `03_malha_ibge_dtb.gpkg` |
| 02.01 | `01_icm_s2id.xlsx` · `02_atlas_sumariza.xlsx` | `01_icm_desastres.xlsx` |
| 02.02 | `03_malha_ibge_dtb.gpkg` · `01_icm_desastres.xlsx` | **`municipios_brasil.shp`** + `.gpkg` |
| 03.01 | `municipios_brasil.gpkg` | **`municipios_rmvale.shp`** + `.gpkg` + `.xlsx` |

## Decisões importantes

- **Geometria só em formato geográfico.** O polígono vem do shapefile do IBGE e
  nunca passa por Excel: uma célula do Excel guarda no máximo 32.767 caracteres,
  e a antiga `5.Base_Mescla_IBGE_MUN.xlsx` tinha 40 municípios com o contorno cortado.
- **S2iD cruzado pelo código IBGE**, não pelo nome (pelo nome, 122 municípios
  homônimos ficavam errados).
- **Classificação do ICM = faixa do arquivo oficial** (A, B, C ou D), em vez de
  recalculada pelas regras de corte.
- **Municípios sem desastre no Atlas** ficam com danos = 0 e `possui_registro_atlas = 0`.
- **Lagoa Mirim e Lagoa dos Patos** (códigos 4300001 e 4300002) saem da malha.
- **Boa Esperança do Norte (MT, 5101837)** tem polígono e DTB, mas não está no ICM
  nem no Atlas: fica com esses campos vazios.
- **Nomes de coluna no shapefile** têm no máximo 10 caracteres (limite do formato).
  O nome completo de cada coluna está em `dicionario_colunas_shapefile.csv`, e o
  `municipios_brasil.gpkg` tem o mesmo conteúdo com os nomes completos.

## Recorte da RMVale

O filtro usa a coluna `sub_regiao_sp` da DTB: as sub-regiões SR1 a SR5 são
exatamente os 39 municípios da RMVale (SR5 = Litoral Norte). O script para com
erro se o recorte não tiver 39 municípios.

| Sub-região | Municípios |
|---|---|
| SR1 | Caçapava, Igaratá, Jacareí, Jambeiro, Monteiro Lobato, Paraibuna, Santa Branca, São José dos Campos |
| SR2 | Campos do Jordão, Lagoinha, Natividade da Serra, Pindamonhangaba, Redenção da Serra, Santo Antônio do Pinhal, São Bento do Sapucaí, São Luiz do Paraitinga, Taubaté, Tremembé |
| SR3 | Aparecida, Cachoeira Paulista, Canas, Cunha, Guaratinguetá, Lorena, Piquete, Potim, Roseira |
| SR4 | Arapeí, Areias, Bananal, Cruzeiro, Lavrinhas, Queluz, São José do Barreiro, Silveiras |
| SR5 | Caraguatatuba, Ilhabela, São Sebastião, Ubatuba |

## Atlas de Desastres

O Atlas bruto (`BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.xlsx`) não está no
repositório. Enquanto ele não for colocado em `dados/entrada/`, a etapa 01.02 usa a
base já sumarizada `atlas_sumariza_2013_em_diante.xlsx`. Com o arquivo bruto na
pasta, o script refaz a sumarização seguindo as regras de agregação do dicionário
de dados (Sum, Moda, Drop).
