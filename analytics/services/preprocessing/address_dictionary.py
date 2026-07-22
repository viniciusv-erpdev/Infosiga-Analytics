def build_address_dictionary(clusters):
    """Constrói um dicionário que mapeia variações para o nome canônico."""
    dictionary = {}
    for canonico, grupo in clusters.items():
        for variacao in grupo.get("variacoes", []):
            dictionary[variacao] = canonico
        if canonico not in dictionary:
            dictionary[canonico] = canonico
    return dictionary
