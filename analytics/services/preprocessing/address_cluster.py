from collections import Counter

from analytics.services.preprocessing.similarity import similarity_score


TIPOS_DE_VIA = {"rua", "avenida", "rodovia", "estrada"}
SIMILARITY_THRESHOLD = 90


def _grouping_key(logradouro):
    primeiro_token = logradouro.split()[0] if logradouro.split() else ""

    if primeiro_token in TIPOS_DE_VIA:
        return ("TIPO_VIA", primeiro_token)

    return ("PREFIXO_DESCONHECIDO", primeiro_token)


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
        chave_agrupamento = _grouping_key(candidato)

        # Encontra o melhor representante existente com maior similaridade
        melhor_representante = None
        melhor_score = -1
        for representante, grupo in clusters.items():
            # Tipos conhecidos não se misturam. Para entradas sem tipo
            # reconhecido, exige o mesmo primeiro token como proteção.
            if _grouping_key(representante) != chave_agrupamento:
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
