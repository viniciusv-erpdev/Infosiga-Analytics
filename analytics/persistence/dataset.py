from typing import Optional

from django.contrib.auth import get_user_model

from analytics.models import Dataset


User = get_user_model()


def create_dataset(
    usuario,
    nome_original: str,
    arquivo,
    quantidade_registros: int = 0,
) -> Dataset:
    return Dataset.objects.create(
        usuario=usuario,
        nome_original=nome_original,
        arquivo=arquivo,
        quantidade_registros=quantidade_registros,
    )


def get_dataset(
    dataset_id: int,
    usuario,
) -> Optional[Dataset]:
    return (
        Dataset.objects
        .filter(
            id=dataset_id,
            usuario=usuario,
        )
        .first()
    )