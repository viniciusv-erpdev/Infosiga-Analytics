from analytics.services.preprocessing.address_matcher import regularize_addresses
from analytics.services.preprocessing.address_normalizer import normalize_address
from analytics.services.preprocessing.address_semantic_cleaner import clean_semantic_address
from analytics.services.preprocessing.apply_manual_corrections import apply_manual_corrections
from uuid import uuid4

def run_preprocessing(df):
    """Executa o pipeline completo de pré-processamento dos logradouros."""
    if df is None:
        return df

    df_processado = df.copy()

    if "id_registro" not in df_processado.columns:
        df_processado["id_registro"] = [
            str(uuid4())
            for _ in range(len(df_processado))
        ]

    if "logradouro" in df_processado.columns:
        df_processado["logradouro_normalizado"] = (
            df_processado["logradouro"].apply(normalize_address)
        )
    else:
        df_processado["logradouro_normalizado"] = ""

    df_processado["logradouro_limpo"] = (
        df_processado["logradouro_normalizado"]
        .apply(clean_semantic_address)
    )

    df_processado = apply_manual_corrections(df_processado)

    df_processado = regularize_addresses(df_processado)

    return df_processado