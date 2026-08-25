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

EXPANSOES_SEMANTICAS = {
    "pres": "presidente",
    "dep": "deputado",
    "dr": "doutor",
    "cel": "coronel",
    "estr": "estrada",
    "prof": "professor",
}

APOSTROPHE_VARIANTS = {
    "'",
    "´",
    "’",
    "‘",
    "`",
}

def _expandir_abreviacoes_semanticas(tokens):
    tokens_expandidos = []

    for token in tokens:
        substituto = EXPANSOES_SEMANTICAS.get(token, token)

        if tokens_expandidos and tokens_expandidos[-1] == substituto:
            continue

        tokens_expandidos.append(substituto)

    return tokens_expandidos


def normalize_address(logradouro):
    """Normaliza um logradouro para um formato simples e consistente."""
    if pd.isna(logradouro):
        return ""

    if not isinstance(logradouro, str):
        logradouro = str(logradouro)

    texto = logradouro.strip().lower()
    if not texto:
        return ""

    texto = normalize_apostrophes(texto)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = texto.replace(".", " ")
    texto = texto.replace("-", " ")
    texto = re.sub(r"\s+", " ", texto).strip()

    if not texto:
        return ""

    tokens = texto.split()
    tokens_normalizados = [ABREVIACOES.get(token, token) for token in tokens]
    tokens_expandidos = _expandir_abreviacoes_semanticas(tokens_normalizados)
    return " ".join(tokens_expandidos)

def normalize_apostrophes(value):
    if not isinstance(value, str):
        return value

    for char in APOSTROPHE_VARIANTS:
        value = value.replace(char, "")

    return value
