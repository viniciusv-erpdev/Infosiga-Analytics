from rapidfuzz import fuzz


def similarity_score(a, b):
    """Retorna o score de similaridade entre dois logradouros."""
    if not a and not b:
        return 100

    return fuzz.token_sort_ratio(a, b)
