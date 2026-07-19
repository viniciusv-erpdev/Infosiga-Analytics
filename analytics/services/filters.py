import pandas as pd


def apply_filters(df, tipo_via=None, tipo_sinistro=None):
    """Aplica filtros iniciais e opcionais ao DataFrame."""
    if df is None:
        return df

    df_filtered = df.copy()

    if "tipo_registro" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["tipo_registro"] != "NOTIFICACAO"]

    if "municipio" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["municipio"] == "RIBEIRAO PRETO"]

    if tipo_via == "urbana" and "tipo_via" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["tipo_via"] == "VIAS URBANAS"]
    elif tipo_via == "estradas e rodovias" and "tipo_via" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["tipo_via"] == "ESTRADAS E RODOVIAS"]

    if tipo_sinistro == "fatal" and "tipo_registro" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["tipo_registro"] == "SINISTRO FATAL"]
    elif tipo_sinistro == "nao_fatal" and "tipo_registro" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["tipo_registro"] == "SINISTRO NAO FATAL"]

    return df_filtered
