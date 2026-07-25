import re


SEMANTIC_RULES = [
    # Remove expressões que não fazem parte do nome principal da via.
    (r"\b(?:trevo de acesso|alça de acesso|alca de acesso|lateral da|marginal da|acesso à|acesso a|acesso|sentido centro|sentido bairro|pista norte|pista sul|viaduto|ponte|passarela|retorno)\b", ""),
    # Remove referências de quilometragem e número.
    (r"\bkm\s*\d+\b", ""),
    (r"\bkm\b", ""),
    (r"\bn[oº]\s*\d+\b", ""),
    (r"\bn[oº]\b", ""),
    # Outras expressões de posição ou localização.
    (r"\bproximo ao\b", ""),
    (r"\bpr[oó]ximo ao\b", ""),
    (r"\bdefronte\b", ""),
    (r"\bem frente ao\b", ""),
]


def clean_semantic_address(logradouro):
    """Remove expressões semânticas determinísticas e preserva o nome principal da via."""
    if not logradouro:
        return ""

    texto = str(logradouro).strip().lower()
    if not texto:
        return ""

    for pattern, replacement in SEMANTIC_RULES:
        texto = re.sub(pattern, replacement, texto)

    texto = re.sub(r"\s+", " ", texto).strip()
    texto = re.sub(r"\s*,\s*", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto
