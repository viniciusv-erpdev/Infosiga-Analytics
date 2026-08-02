import pandas as pd

from analytics.services.preprocessing.address_cluster import cluster_addresses
from analytics.services.preprocessing.address_dictionary import build_address_dictionary
from analytics.services.preprocessing.similarity import similarity_score


def regularize_addresses(df):
    """Cria colunas canônicas e de similaridade para os logradouros limpos.

    Usa exclusivamente 'logradouro_limpo' como fonte verdade para agrupamento e
    atribuição canônica. Registros já protegidos por uma correção manual
    mantêm o valor de 'logradouro_canonico' sem sofrer sobrescrita automática.
    """
    if df is None:
        return df

    df_processado = df.copy()

    if "logradouro_canonico" not in df_processado.columns:
        df_processado["logradouro_canonico"] = ""

    if "logradouro_limpo" in df_processado.columns:
        valores_limpos = df_processado["logradouro_limpo"].fillna("")
    elif "logradouro_normalizado" in df_processado.columns:
        valores_limpos = df_processado["logradouro_normalizado"].fillna("")
    else:
        valores_limpos = pd.Series([""] * len(df_processado))

    df_processado["logradouro_limpo"] = valores_limpos

    # Registros protegidos não participam do agrupamento automático
    protegidos = df_processado["logradouro_canonico"].notna() & df_processado["logradouro_canonico"].astype(str).str.strip().ne("")

    valores_para_cluster = [
        valor for valor, protegido in zip(valores_limpos, protegidos) if valor and not protegido
    ]

    clusters = cluster_addresses(valores_para_cluster)
    dictionary = build_address_dictionary(clusters)

    # Atribui o canônico automaticamente apenas para registros não protegidos
    def atribuir_canonico(valor, protegido, canonico_existente):
        if protegido:
            return canonico_existente
        return dictionary.get(valor, valor)

    df_processado["logradouro_canonico"] = df_processado.apply(
        lambda row: atribuir_canonico(row["logradouro_limpo"], protegidos.loc[row.name], row["logradouro_canonico"]),
        axis=1,
    )

    # Similaridade é calculada somente para registros processados automaticamente
    df_processado["similaridade"] = df_processado.apply(
        lambda row: None if protegidos.loc[row.name] else similarity_score(row["logradouro_limpo"], row["logradouro_canonico"]),
        axis=1,
    )

    # Frequência do grupo representa a frequência do valor canônico final no DataFrame
    frequencias = df_processado["logradouro_canonico"].dropna().str.strip()
    df_processado["frequencia_grupo"] = frequencias.apply(
        lambda valor: int((frequencias == valor).sum()) if valor else 0
    )

    return df_processado
