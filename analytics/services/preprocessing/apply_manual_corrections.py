import pandas as pd

from analytics.persistence.corrections import get_correction_by_limpo


def apply_manual_corrections(df):
    """Aplica correções manuais persistidas ao DataFrame sem modificar os dados originais.

    A função consulta o banco por meio de ``get_correction_by_limpo`` usando a
    coluna ``logradouro_limpo`` como chave. Somente correções com status
    aprovado são aplicadas e o valor resultante é preenchido em
    ``logradouro_canonico``. O DataFrame original não é alterado in-place.
    """
    if df is None:
        return None

    df_processado = df.copy()

    df_processado["logradouro_canonico"] = ""

    if "logradouro_limpo" not in df_processado.columns:
        return df_processado

    df_processado["logradouro_canonico"] = ""

    cache = {}
    for index, row in df_processado.iterrows():
        logradouro_limpo = row.get("logradouro_limpo")

        if pd.isna(logradouro_limpo):
            continue

        if not isinstance(logradouro_limpo, str):
            logradouro_limpo = str(logradouro_limpo)

        logradouro_limpo = logradouro_limpo.strip()
        if not logradouro_limpo:
            continue

        if logradouro_limpo not in cache:
            correcao = get_correction_by_limpo(logradouro_limpo)
            cache[logradouro_limpo] = correcao

        correcao = cache[logradouro_limpo]
        if correcao is None:
            continue

        if getattr(correcao, "status", None) == "APROVADO":
            df_processado.at[index, "logradouro_canonico"] = getattr(correcao, "logradouro_canonico", "")

    return df_processado
