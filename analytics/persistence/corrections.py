from typing import Optional
from analytics.models import AddressCorrection

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