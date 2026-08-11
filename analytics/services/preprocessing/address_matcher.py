import pandas as pd

from analytics.services.preprocessing.address_cluster import cluster_addresses
from analytics.services.preprocessing.address_dictionary import build_address_dictionary
from analytics.services.preprocessing.similarity import similarity_score


def regularize_addresses(df):
    """Cria colunas de sugestão, similaridade e confiança para os logradouros limpos.

    Usa exclusivamente 'logradouro_limpo' como fonte verdade para agrupamento e
    atribuição de sugestão automática. Registros protegidos por uma correção
    manual mantêm o valor de 'logradouro_canonico' sem sofrer sobrescrita
    automática. A coluna 'logradouro_sugerido' representa apenas a sugestão
    do matcher e não deve ser usada como correção manual.
    """
    if df is None:
        return df

    df_processado = df.copy()

    if "logradouro_canonico" not in df_processado.columns:
        df_processado["logradouro_canonico"] = ""

    if "logradouro_sugerido" not in df_processado.columns:
        df_processado["logradouro_sugerido"] = ""

    if "correcao_manual_aplicada" not in df_processado.columns:
        df_processado["correcao_manual_aplicada"] = False

    if "logradouro_limpo" in df_processado.columns:
        valores_limpos = df_processado["logradouro_limpo"].fillna("")
    elif "logradouro_normalizado" in df_processado.columns:
        valores_limpos = df_processado["logradouro_normalizado"].fillna("")
    else:
        valores_limpos = pd.Series([""] * len(df_processado))

    df_processado["logradouro_limpo"] = valores_limpos

    # Registros protegidos não participam do agrupamento automático
    protegidos = df_processado["correcao_manual_aplicada"].fillna(False).astype(bool)

    valores_para_cluster = [
        valor for valor, protegido in zip(valores_limpos, protegidos) if valor and not protegido
    ]

    clusters = cluster_addresses(valores_para_cluster)
    dictionary = build_address_dictionary(clusters)

    def obter_sugerido(valor):
        if not valor:
            return ""
        return dictionary.get(valor, valor)

    df_processado["logradouro_sugerido"] = df_processado["logradouro_limpo"].apply(obter_sugerido)

    def atribuir_canonico(protegido, canonico_existente):
        if protegido:
            return canonico_existente
        return ""

    df_processado["logradouro_canonico"] = df_processado.apply(
        lambda row: atribuir_canonico(row["correcao_manual_aplicada"], row["logradouro_canonico"]),
        axis=1,
    )

    # Similaridade é calculada somente para registros processados automaticamente
    df_processado["similaridade"] = df_processado.apply(
        lambda row: None if protegidos.loc[row.name] else similarity_score(row["logradouro_limpo"], row["logradouro_sugerido"]),
        axis=1,
    )

    def classificar_confianca(valor_limpo, valor_sugerido, protegido, similaridade):
        if protegido:
            return "MANUAL"

        valor_limpo = "" if pd.isna(valor_limpo) else str(valor_limpo).strip()
        valor_sugerido = "" if pd.isna(valor_sugerido) else str(valor_sugerido).strip()

        if not valor_limpo:
            return "BAIXA"

        if valor_limpo == valor_sugerido:
            return "EXATO"

        if pd.isna(similaridade):
            return "BAIXA"

        try:
            valor_similaridade = float(similaridade)
        except (TypeError, ValueError):
            return "BAIXA"

        if valor_similaridade >= 98:
            return "ALTA"
        if valor_similaridade >= 90:
            return "MEDIA"
        return "BAIXA"

    df_processado["confianca_matching"] = df_processado.apply(
        lambda row: classificar_confianca(
            row["logradouro_limpo"],
            row["logradouro_sugerido"],
            protegidos.loc[row.name],
            row["similaridade"],
        ),
        axis=1,
    )

    # Frequência do grupo representa a frequência da sugestão de matching automático
    frequencias = df_processado["logradouro_sugerido"].dropna().str.strip()
    df_processado["frequencia_grupo"] = frequencias.apply(
        lambda valor: int((frequencias == valor).sum()) if valor else 0
    )

    return df_processado
