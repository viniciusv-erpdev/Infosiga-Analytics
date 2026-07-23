from analytics.services.preprocessing.address_matcher import regularize_addresses
from analytics.services.preprocessing.address_normalizer import normalize_address
from analytics.services.preprocessing.address_semantic_cleaner import clean_semantic_address


def run_preprocessing(df):
    """Executa a normalização, limpeza semântica e regularização de logradouros sem alterar o logradouro original."""
    if df is None:
        return df

    df_processado = df.copy()

    if "logradouro" in df_processado.columns:
        df_processado["logradouro_normalizado"] = df_processado["logradouro"].apply(normalize_address)
    else:
        df_processado["logradouro_normalizado"] = ""

    if "logradouro_normalizado" in df_processado.columns:
        df_processado["logradouro_limpo"] = df_processado["logradouro_normalizado"].apply(clean_semantic_address)
    else:
        df_processado["logradouro_limpo"] = ""

    return regularize_addresses(df_processado)
