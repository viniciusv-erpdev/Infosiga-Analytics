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
        # Verifica se já existe correção aprovada
        approved = persistence.get_approved_correction_by_limpo(logradouro_limpo)

        # Busca a correção mais recente (se existir)
        current = persistence.get_correction_by_limpo(logradouro_limpo)

        # Se não existe correção atual, cria uma
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

        # Se existe correção aprovada e a submissão não é APROVADA,
        # não sobrescrever a correção aprovada; registrar auditoria apenas.
        if approved is not None and status != "APROVADO":
            # cria auditoria sem aplicar atualização
            persistence.update_correction_with_audit(
                approved,
                apply_update=False,
                autor=autor,
                origin=origin,
                note=note,
                logradouro_canonico=logradouro_canonico,
                status=status,
            )
            return approved

        # Caso contrário, atualiza o registro atual (ou o aprovado) com auditoria
        target = approved if (approved is not None and status == "APROVADO") else current

        return persistence.update_correction_with_audit(
            target,
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
