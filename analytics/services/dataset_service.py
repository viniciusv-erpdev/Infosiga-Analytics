import logging

from django.db import transaction

from analytics.persistence import datasets as dataset_persistence
from analytics.services.address_correction_service import (AddressCorrectionService,)

logger = logging.getLogger(__name__)

class DatasetService:

    @staticmethod
    def create_from_upload(
        usuario,
        arquivo,
        quantidade_registros,
    ):
        return dataset_persistence.create_dataset(
            usuario=usuario,
            nome_original=arquivo.name,
            arquivo=arquivo,
            quantidade_registros=quantidade_registros,
        )

    @staticmethod
    def save_processed_dataframe(
        dataset,
        dataframe,
    ):
        return dataset_persistence.save_processed_dataframe(
            dataset=dataset,
            dataframe=dataframe,
        )

    @staticmethod
    def load_processed_dataframe(dataset):
        return dataset_persistence.load_processed_dataframe(
            dataset=dataset
        )

    @staticmethod
    def list_for_user(usuario):
        return dataset_persistence.list_datasets_for_user(usuario)

    @staticmethod
    def get_for_user(dataset_id, usuario):
        return dataset_persistence.get_dataset_for_user(dataset_id, usuario)

    @staticmethod
    def prepare_dataframe_for_export(dataset):
        dataframe = DatasetService.load_processed_dataframe(dataset)

        columns_to_remove = [
            "logradouro_normalizado",
            "logradouro_limpo",
        ]

        dataframe = dataframe.drop(
            columns=columns_to_remove,
            errors="ignore",
        )

        priority_columns = [
            "logradouro",
            "logradouro_sugerido",
            "logradouro_canonico",
            "correcao_manual_aplicada",
            "similaridade",
            "confianca_matching",
            "frequencia_grupo",
        ]

        existing_priority_columns = [
            column
            for column in priority_columns
            if column in dataframe.columns
        ]

        remaining_columns = [
            column
            for column in dataframe.columns
            if column not in existing_priority_columns
        ]

        if "correcao_manual_aplicada" in dataframe.columns:
            dataframe["correcao_manual_aplicada"] = (
                dataframe["correcao_manual_aplicada"]
                .map({
                    True: "Sim",
                    False: "Não",
                })
                .fillna("")
            )    

        return dataframe[
            existing_priority_columns + remaining_columns
        ]

    @staticmethod
    def delete(dataset):
        dataset_persistence.delete_dataset(dataset)

    @staticmethod
    def update_record(
        dataset,
        id_registro,
        updates,
        usuario,
        note="",
    ):
        original_dataframe = (
            dataset_persistence.load_processed_dataframe(dataset)
        )

        try:
            with transaction.atomic():
                return DatasetService._update_record(
                    dataset=dataset,
                    id_registro=id_registro,
                    updates=updates,
                    usuario=usuario,
                    note=note,
                )
        except Exception:
            logger.exception(
                "Falha ao atualizar registro; restaurando Parquet. dataset_id=%s id_registro=%s usuario_id=%s",
                dataset.id,
                id_registro,
                getattr(usuario, "id", None),
            )
            try:
                dataset_persistence.save_processed_dataframe(
                    dataset=dataset,
                    dataframe=original_dataframe,
                )
            except Exception:
                logger.exception(
                    "Falha ao restaurar Parquet após erro de atualização. dataset_id=%s id_registro=%s",
                    dataset.id,
                    id_registro,
                )
                raise
            raise

    @staticmethod
    def _update_record(
        dataset,
        id_registro,
        updates,
        usuario,
        note="",
    ):
        current_record = dataset_persistence.get_dataframe_record(
            dataset=dataset,
            id_registro=id_registro,
        )

        previous_canonico = (
            ""
            if current_record.get("logradouro_canonico") is None
            else str(
                current_record.get("logradouro_canonico")
            ).strip()
        )

        new_canonico = updates.get("logradouro_canonico")

        canonical_changed = (
            "logradouro_canonico" in updates
            and new_canonico is not None
            and str(new_canonico).strip() != previous_canonico
        )

        # Alterações que não envolvem logradouro_canonico
        # continuam utilizando exatamente o fluxo existente.
        if not canonical_changed:
            return dataset_persistence.update_dataframe_record(
                dataset=dataset,
                id_registro=id_registro,
                updates=updates,
                usuario=usuario,
                note=note,
            )

        new_canonico = str(new_canonico).strip()

        if not new_canonico:
            raise ValueError(
                "logradouro_canonico não pode ser vazio."
            )

        logradouro_limpo = (
            ""
            if current_record.get("logradouro_limpo") is None
            else str(
                current_record.get("logradouro_limpo")
            ).strip()
        )

        if not logradouro_limpo:
            raise ValueError(
                "O registro não possui logradouro_limpo."
            )

        # Primeiro propaga a alteração para todos os registros
        # equivalentes dentro deste dataset.
        dataset = (
            dataset_persistence.update_dataframe_records_by_limpo(
                dataset=dataset,
                logradouro_limpo=logradouro_limpo,
                logradouro_canonico=new_canonico,
                usuario=usuario,
                note=note,
            )
        )

        # Depois mantém a AddressCorrection como regra persistente
        # para o logradouro_limpo.
        AddressCorrectionService.apply_manual_correction(
            logradouro_original=current_record.get(
                "logradouro",
                "",
            ),
            logradouro_limpo=logradouro_limpo,
            logradouro_canonico=new_canonico,
            usuario=usuario,
            note=note,
        )

        return dataset
