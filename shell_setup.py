import os
from pathlib import Path

import pandas as pd
from django.conf import settings

from analytics.models import AddressCorrection
from analytics.persistence.corrections import get_correction_by_limpo
from analytics.services.preprocessing.address_normalizer import normalize_address
from analytics.services.preprocessing.address_matcher import regularize_addresses
from analytics.services.preprocessing.pipeline import run_preprocessing

# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = settings.BASE_DIR


# ============================================================
# UTILITÁRIOS
# ============================================================

def cls():
    os.system("cls" if os.name == "nt" else "clear")


def carregar_dados_locais(nome_arquivo="sinistros_teste.csv"):
    caminho = BASE_DIR / "dados_locais" / nome_arquivo

    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        return None

    return pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1"
    )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

# Para carregar o arquivo de configuração do shell
#exec(open("shell_setup.py", encoding="utf-8").read())

# Para carregar dados:
# df = carregar_dados_locais()