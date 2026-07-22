from analytics.services.preprocessing.address_matcher import regularize_addresses
from analytics.services.preprocessing.address_normalizer import normalize_address


def run_preprocessing(df):
    """Executa a normalização e a regularização de logradouros sem alterar o logradouro original."""
    if df is None:
        return df

    df_processado = df.copy()

    if "logradouro" in df_processado.columns:
        df_processado["logradouro_normalizado"] = df_processado["logradouro"].apply(normalize_address)
    else:
        df_processado["logradouro_normalizado"] = ""

    return regularize_addresses(df_processado)
