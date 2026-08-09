from typing import Optional

from analytics.persistence import corrections as persistence


class ReviewService:
    """Serviço que encapsula a lógica de criação/atualização de correções.

    Regras principais:
    - Uma correção APROVADA pode substituir o estado atual.
    - PENDENTE/REJEITADO nunca sobrescrevem uma correção APROVADA ativa.
    - Toda escrita e auditoria é delegada à camada `persistence`.
    """

    @staticmethod
    def submit_correction(
        logradouro_original: str,
        logradouro_limpo: str,
        logradouro_canonico: str,
        status: str = "PENDENTE",
        origem: str = "MANUAL",
        score_similaridade: Optional[float] = None,
        autor: str = "",
        origin: str = "UI",
        note: str = "",
    ):
        if not logradouro_limpo:
            raise ValueError("logradouro_limpo é obrigatório")

        current = persistence.get_correction_by_limpo(logradouro_limpo)

        # Primeira correção para este logradouro
        if current is None:
            return persistence.save_correction_with_audit(
                logradouro_original=logradouro_original,
                logradouro_limpo=logradouro_limpo,
                logradouro_canonico=logradouro_canonico,
                status=status,
                origem=origem,
                score_similaridade=score_similaridade,
                autor=autor,
                origin=origin,
                note=note,
            )

        # Correção já existente: atualiza o mesmo registro
        return persistence.update_correction_with_audit(
            current,
            logradouro_canonico=logradouro_canonico,
            status=status,
            autor=autor,
            origin=origin,
            note=note,
        )
