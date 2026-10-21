# -*- coding: utf-8 -*-
"""
Roda o pipeline completo, na ordem, parando no primeiro erro.

Uso:  python executar_pipeline.py
"""

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

ETAPAS = [
    "01_extracao_e_tratamento/01_icm_s2id.py",
    "01_extracao_e_tratamento/02_atlas_sumariza.py",
    "01_extracao_e_tratamento/03_ibge_malha_dtb.py",
    "02_consolidacao_e_merge/01_merge_icm_desastres.py",
    "02_consolidacao_e_merge/02_merge_shapefile_final.py",
]

for etapa in ETAPAS:
    print(f"\n################ {etapa}")
    resultado = subprocess.run([sys.executable, str(RAIZ / etapa)])
    if resultado.returncode != 0:
        sys.exit(f"\nFalhou em: {etapa}")

print("\nPipeline concluído.")
