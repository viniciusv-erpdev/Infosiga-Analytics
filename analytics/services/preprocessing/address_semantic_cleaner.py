import re


SEMANTIC_RULES = [
    (r"\b(?:lateral da|marginal da|alça de acesso|alca de acesso|acesso à|acesso a|trevo de acesso|sentido centro|sentido bairro|pista norte|pista sul)\b", ""),
    (r"\bkm\s*\d+\b", ""),
    (r"\bnº\s*\d+\b", ""),
    (r"\bpróximo ao\b", ""),
    (r"\bproximo ao\b", ""),
    (r"\bdefronte\b", ""),
    (r"\bem frente ao\b", ""),
    (r"\bda\b", ""),
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
