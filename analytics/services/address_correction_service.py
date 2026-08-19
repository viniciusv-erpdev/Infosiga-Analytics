from analytics.persistence import corrections as corrections_persistence


class AddressCorrectionService:
    """
    Coordena a aplicação de uma correção manual de logradouro
    originada pela edição de um Dataset.

    A persistência de AddressCorrection e CorrectionAudit permanece
    na camada de persistence.
    """

    @staticmethod
    def apply_manual_correction(
        *,
        logradouro_original: str,
        logradouro_limpo: str,
        logradouro_canonico: str,
        usuario,
        note: str = "",
    ):
        if not logradouro_limpo:
            return None

        if not logradouro_canonico:
            return None

        existing_correction = (
            corrections_persistence.get_correction_by_limpo(
                logradouro_limpo
            )
        )

        if existing_correction:
            return corrections_persistence.update_correction_with_audit(
                correction=existing_correction,
                autor=str(usuario),
                origin="DATASET",
                note=note,
                logradouro_canonico=logradouro_canonico,
                status="APROVADO",
            )

        return corrections_persistence.save_correction_with_audit(
            logradouro_original=str(logradouro_original or ""),
            logradouro_limpo=logradouro_limpo,
            logradouro_canonico=logradouro_canonico,
            status="APROVADO",
            origem="MANUAL",
            autor=str(usuario),
            origin="DATASET",
            note=note,
        )