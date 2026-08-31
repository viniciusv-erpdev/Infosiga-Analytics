from analytics.persistence.corrections import (
    get_approved_corrections_by_limpos,
)


def apply_manual_corrections(df):
    """Aplica correções manuais aprovadas ao DataFrame.

    As correções são consultadas em lote no banco utilizando
    `logradouro_limpo` como chave. Somente correções com status
    APROVADO são aplicadas.
    """

    if df is None:
        return None

    df_processado = df.copy()

    if "logradouro_canonico" not in df_processado.columns:
        df_processado["logradouro_canonico"] = ""

    if "correcao_manual_aplicada" not in df_processado.columns:
        df_processado["correcao_manual_aplicada"] = False

    if "logradouro_limpo" not in df_processado.columns:
        return df_processado

    # Obtém os logradouros válidos presentes no DataFrame.
    limpos = (
        df_processado["logradouro_limpo"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    limpos_unicos = limpos[limpos != ""].unique().tolist()

    if not limpos_unicos:
        return df_processado

    # Uma única consulta ao banco.
    correcoes = get_approved_corrections_by_limpos(limpos_unicos)

    if not correcoes:
        return df_processado

    # Cria um mapa:
    # "avenida caramuru" -> "Avenida Caramuru"
    mapa_correcoes = {
        logradouro_limpo: correction.logradouro_canonico
        for logradouro_limpo, correction in correcoes.items()
    }

    # Identifica quais registros possuem correção manual aprovada.
    mask = limpos.isin(mapa_correcoes)

    # Aplica o nome canônico.
    df_processado.loc[mask, "logradouro_canonico"] = (
        limpos[mask].map(mapa_correcoes)
    )

    # Marca os registros afetados.
    df_processado.loc[mask, "correcao_manual_aplicada"] = True

    return df_processado
