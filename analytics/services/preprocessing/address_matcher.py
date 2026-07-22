from analytics.services.preprocessing.address_cluster import cluster_addresses
from analytics.services.preprocessing.address_dictionary import build_address_dictionary
from analytics.services.preprocessing.address_normalizer import normalize_address
from analytics.services.preprocessing.similarity import similarity_score


def regularize_addresses(df):
    """Cria colunas canônicas e de similaridade para os logradouros normalizados."""
    if df is None:
        return df

    df_processado = df.copy()

    if "logradouro_normalizado" not in df_processado.columns:
        df_processado["logradouro_normalizado"] = ""

    valores_normalizados = df_processado["logradouro_normalizado"].fillna("")

    df_processado["logradouro_normalizado"] = valores_normalizados

    normalizados = [valor for valor in valores_normalizados if valor]
    clusters = cluster_addresses(normalizados)
    dictionary = build_address_dictionary(clusters)

    df_processado["logradouro_canonico"] = df_processado["logradouro_normalizado"].apply(
        lambda valor: dictionary.get(valor, valor)
    )

    df_processado["similaridade"] = df_processado.apply(
        lambda row: similarity_score(row["logradouro_normalizado"], row["logradouro_canonico"]),
        axis=1,
    )

    grupos = {valor: grupo["frequencia"] for valor, grupo in clusters.items()}
    df_processado["frequencia_grupo"] = df_processado["logradouro_canonico"].apply(
        lambda valor: grupos.get(valor, 0)
    )

    return df_processado
