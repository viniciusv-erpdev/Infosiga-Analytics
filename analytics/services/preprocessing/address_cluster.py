from collections import Counter

from analytics.services.preprocessing.similarity import similarity_score


TIPOS_DE_VIA = {"rua", "avenida", "rodovia", "estrada"}
SIMILARITY_THRESHOLD = 90


def cluster_addresses(lista_logradouros):
    """Agrupa logradouros limpos por similaridade e frequência.

    Retorna um dicionário onde cada chave é o nome canônico e o valor contém:
    - 'canonico': nome canônico
    - 'frequencia': soma das frequências dos membros
    - 'membros': lista dos logradouros limpos pertencentes ao cluster
    """
    if not lista_logradouros:
        return {}

    entradas = [logradouro for logradouro in lista_logradouros if logradouro]
    if not entradas:
        return {}

    # Frequência de cada logradouro limpo
    frequencias = Counter(entradas)
    # Ordena por frequência decrescente e nome para estabilidade
    logradouros_ordenados = sorted(
        frequencias.items(), key=lambda item: (-item[1], item[0])
    )

    clusters = {}

    for candidato, frequencia in logradouros_ordenados:
        tipo_via = candidato.split()[0] if candidato.split() else ""
        if tipo_via not in TIPOS_DE_VIA:
            # Ignora entradas sem um tipo de via conhecido
            continue

        # Encontra o melhor representante existente com maior similaridade
        melhor_representante = None
        melhor_score = -1
        for representante, grupo in clusters.items():
            # Mantém correspondência por tipo de via para evitar misturas
            rep_tipo_via = representante.split()[0] if representante.split() else ""
            if rep_tipo_via != tipo_via:
                continue

            score = similarity_score(candidato, representante)
            if score > melhor_score:
                melhor_score = score
                melhor_representante = representante

        # Se o melhor representante ultrapassa o limiar, agrupa nele
        if melhor_score >= SIMILARITY_THRESHOLD and melhor_representante is not None:
            grupo = clusters[melhor_representante]
            grupo["frequencia"] += frequencia
            if candidato not in grupo["membros"]:
                grupo["membros"].append(candidato)
        else:
            # Cria novo cluster com o próprio candidato como canônico
            clusters[candidato] = {
                "canonico": candidato,
                "frequencia": frequencia,
                "membros": [candidato],
            }

    # Normaliza a estrutura de saída: chave -> objeto do grupo
    resultado = {}
    for chave, grupo in clusters.items():
        resultado[grupo["canonico"]] = {
            "canonico": grupo["canonico"],
            "frequencia": grupo["frequencia"],
            "membros": grupo["membros"],
        }

    return resultado
