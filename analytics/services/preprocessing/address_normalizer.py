import re
import unicodedata

import pandas as pd


ABREVIACOES = {
    "av": "avenida",
    "av.": "avenida",
    "r": "rua",
    "r.": "rua",
    "rod": "rodovia",
    "rod.": "rodovia",
    "est": "estrada",
    "est.": "estrada",
}


def normalize_address(logradouro):
    """Normaliza um logradouro para um formato simples e consistente."""
    if pd.isna(logradouro):
        return ""

    if not isinstance(logradouro, str):
        logradouro = str(logradouro)

    texto = logradouro.strip().lower()
    if not texto:
        return ""

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = texto.replace(".", " ")
    texto = texto.replace("-", " ")
    texto = re.sub(r"\s+", " ", texto).strip()

    if not texto:
        return ""

    tokens = texto.split()
    tokens_normalizados = [ABREVIACOES.get(token, token) for token in tokens]
    return " ".join(tokens_normalizados)
