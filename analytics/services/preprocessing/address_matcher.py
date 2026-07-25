import pandas as pd

from analytics.services.preprocessing.address_cluster import cluster_addresses
from analytics.services.preprocessing.address_dictionary import build_address_dictionary
from analytics.services.preprocessing.similarity import similarity_score


def regularize_addresses(df):
    """Cria colunas canônicas e de similaridade para os logradouros limpos.

    Usa exclusivamente 'logradouro_limpo' como fonte verdade para agrupamento e
    atribuição canônica.
    """
    if df is None:
        return df

    df_processado = df.copy()

    # Garante que exista a coluna logradouro_limpo com valores preenchidos
    if "logradouro_limpo" in df_processado.columns:
        valores_limpos = df_processado["logradouro_limpo"].fillna("")
    elif "logradouro_normalizado" in df_processado.columns:
        valores_limpos = df_processado["logradouro_normalizado"].fillna("")
    else:
        valores_limpos = pd.Series([""] * len(df_processado))

    df_processado["logradouro_limpo"] = valores_limpos

    logradouros_limpos = [v for v in valores_limpos if v]

    clusters = cluster_addresses(logradouros_limpos)
    dictionary = build_address_dictionary(clusters)

    # Atribui o canônico baseado estritamente no dicionário construído
    df_processado["logradouro_canonico"] = df_processado["logradouro_limpo"].apply(
        lambda valor: dictionary.get(valor, valor)
    )

    # Calcula similaridade entre o valor limpo e o canônico atribuído
    df_processado["similaridade"] = df_processado.apply(
        lambda row: similarity_score(row["logradouro_limpo"], row["logradouro_canonico"]),
        axis=1,
    )

    # Frequência dos grupos baseada na estrutura de clusters
    grupos = {canon: grupo["frequencia"] for canon, grupo in clusters.items()}
    df_processado["frequencia_grupo"] = df_processado["logradouro_canonico"].apply(
        lambda valor: grupos.get(valor, 0)
    )

    return df_processado
