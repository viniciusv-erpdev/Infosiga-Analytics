def build_address_dictionary(clusters):
    """Constrói um dicionário que mapeia variações para o nome canônico."""
    dictionary = {}
    for canonico, grupo in clusters.items():
        # 'membros' contém os logradouros limpos pertencentes ao cluster
        for membro in grupo.get("membros", []):
            dictionary[membro] = canonico
        # garante que o canônico mapeie para si mesmo
        if canonico not in dictionary:
            dictionary[canonico] = canonico
    return dictionary
