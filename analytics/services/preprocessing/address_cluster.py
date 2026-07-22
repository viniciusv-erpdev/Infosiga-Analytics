from collections import Counter

from analytics.services.preprocessing.address_normalizer import normalize_address
from analytics.services.preprocessing.similarity import similarity_score


TIPOS_DE_VIA = {"rua", "avenida", "rodovia", "estrada"}


def cluster_addresses(lista_logradouros):
    """Agrupa logradouros por similaridade e frequência, preservando variações originais."""
    if not lista_logradouros:
        return {}

    entradas = []
    for logradouro in lista_logradouros:
        if not logradouro:
            continue
        normalizado = normalize_address(logradouro)
        if not normalizado:
            continue
        entradas.append((logradouro, normalizado))

    if not entradas:
        return {}

    frequencias = Counter(normalizado for _, normalizado in entradas)
    logradouros_ordenados = sorted(
        frequencias.items(),
        key=lambda item: (-item[1], item[0]),
    )

    clusters = {}
    for normalizado, frequencia in logradouros_ordenados:
        tipo_via = normalizado.split()[0] if normalizado.split() else ""
        if tipo_via not in TIPOS_DE_VIA:
            continue

        existente = None
        for chave, grupo in clusters.items():
            if tipo_via != grupo["tipo_via"]:
                continue

            if similarity_score(normalizado, chave) >= 90:
                existente = chave
                break

        if existente is None:
            clusters[normalizado] = {
                "canonico": normalizado,
                "frequencia": frequencia,
                "variacoes": [
                    original
                    for original, valor_normalizado in entradas
                    if valor_normalizado == normalizado
                ],
                "tipo_via": tipo_via,
            }
            continue

        grupo = clusters[existente]
        grupo["frequencia"] += frequencia
        for original, valor_normalizado in entradas:
            if valor_normalizado == normalizado and original not in grupo["variacoes"]:
                grupo["variacoes"].append(original)

    resultado = {}
    for chave, grupo in clusters.items():
        resultado[grupo["canonico"]] = {
            "canonico": grupo["canonico"],
            "frequencia": grupo["frequencia"],
            "variacoes": grupo["variacoes"],
        }

    return resultado
