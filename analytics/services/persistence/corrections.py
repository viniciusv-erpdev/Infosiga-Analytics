from typing import Optional

from analytics.models import AddressCorrection


def get_correction_by_limpo(logradouro_limpo: str) -> Optional[AddressCorrection]:
    """Retorna uma correção persistida para o `logradouro_limpo`, se existir."""
    if not logradouro_limpo:
        return None

    try:
        return AddressCorrection.objects.filter(logradouro_limpo=logradouro_limpo).order_by("-updated_at").first()
    except Exception:
        return None


def list_manual_corrections(limit: int = 100):
    """Lista correções manuais existentes (limitadas por `limit`)."""
    return AddressCorrection.objects.filter(corrigido_manualmente=True).order_by("-updated_at")[:limit]
