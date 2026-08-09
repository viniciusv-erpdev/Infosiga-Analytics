from typing import Optional
from analytics.models import AddressCorrection, CorrectionAudit

def get_correction_by_limpo(
    logradouro_limpo: str
) -> Optional[AddressCorrection]:

    if not logradouro_limpo:
        return None

    return (
        AddressCorrection.objects
        .filter(logradouro_limpo=logradouro_limpo)
        .order_by("-updated_at")
        .first()
    )


def get_approved_correction_by_limpo(logradouro_limpo: str) -> Optional[AddressCorrection]:
    """Retorna a correção APROVADA mais recente para um `logradouro_limpo`.

    Esta função é usada pelo pipeline para garantir que somente correções
    aprovadas sejam aplicadas.
    """
    if not logradouro_limpo:
        return None

    return (
        AddressCorrection.objects
        .filter(logradouro_limpo=logradouro_limpo, status="APROVADO")
        .order_by("-updated_at")
        .first()
    )


def _create_audit_entry(
    correction: AddressCorrection | None,
    logradouro_limpo: str,
    field_name: str,
    previous_value,
    new_value,
    previous_status: str | None = None,
    new_status: str | None = None,
    autor: str = "",
    origin: str = "",
    note: str = "",
):
    return CorrectionAudit.objects.create(
        correction=correction,
        logradouro_limpo=logradouro_limpo or "",
        field_name=field_name or "",
        previous_value=previous_value,
        new_value=new_value,
        previous_status=previous_status,
        new_status=new_status,
        autor=autor or "",
        origin=origin or "",
        note=note or "",
    )


def save_correction_with_audit(
    logradouro_original: str,
    logradouro_limpo: str,
    logradouro_canonico: str,
    status: str = "PENDENTE",
    origem: str = "MANUAL",
    score_similaridade: float | None = None,
    autor: str = "",
    origin: str = "UI",
    note: str = "",
) -> AddressCorrection:
    """Cria uma nova correção e registra auditoria inicial."""
    correction = save_correction(
        logradouro_original=logradouro_original,
        logradouro_limpo=logradouro_limpo,
        logradouro_canonico=logradouro_canonico,
        status=status,
        origem=origem,
        score_similaridade=score_similaridade,
        autor=autor,
    )

    # Auditoria de criação — previous_value vazio
    _create_audit_entry(
        correction=correction,
        logradouro_limpo=logradouro_limpo,
        field_name="__create__",
        previous_value=None,
        new_value=logradouro_canonico,
        previous_status=None,
        new_status=status,
        autor=autor,
        origin=origin,
        note=note,
    )

    return correction


def update_correction_with_audit(
    correction: AddressCorrection,
    apply_update: bool = True,
    autor: str = "",
    origin: str = "UI",
    note: str = "",
    **fields,
) -> AddressCorrection:

    if correction is None:
        raise ValueError("correction must be provided")

    logradouro_limpo = correction.logradouro_limpo
    previous_status = correction.status

    for field, value in fields.items():

        previous_value = getattr(correction, field, None)

        # Não registra nem aplica alterações inexistentes
        if previous_value == value:
            continue

        new_status = (
            value
            if field == "status"
            else previous_status
        )

        _create_audit_entry(
            correction=correction,
            logradouro_limpo=logradouro_limpo,
            field_name=field,
            previous_value=previous_value,
            new_value=value,
            previous_status=previous_status,
            new_status=new_status,
            autor=autor,
            origin=origin,
            note=note,
        )

        if apply_update:
            setattr(correction, field, value)

    if apply_update:
        correction.save()

    return correction

def save_correction(
    logradouro_original: str,
    logradouro_limpo: str,
    logradouro_canonico: str,
    status: str = "PENDENTE",
    origem: str = "MANUAL",
    score_similaridade: float | None = None,
    autor: str = "",
) -> AddressCorrection:

    return AddressCorrection.objects.create(
        logradouro_original=logradouro_original,
        logradouro_limpo=logradouro_limpo,
        logradouro_canonico=logradouro_canonico,
        status=status,
        origem=origem,
        score_similaridade=score_similaridade,
        autor=autor,
    )

def update_correction(
    correction: AddressCorrection,
    **fields
) -> AddressCorrection:

    for field, value in fields.items():
        setattr(correction, field, value)

    correction.save()

    return correction

def list_corrections(limit: int = 100):
    return (
        AddressCorrection.objects
        .order_by("-updated_at")[:limit]
    )

def list_manual_corrections(limit: int = 100):
    return (
        AddressCorrection.objects
        .filter(
            status="APROVADO",
            origem="MANUAL"
        )
        .order_by("-updated_at")[:limit]
    )

def delete_correction(correction: AddressCorrection):
    correction.delete()