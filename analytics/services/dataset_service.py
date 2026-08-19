from analytics.persistence import datasets as dataset_persistence
from analytics.services.address_correction_service import (AddressCorrectionService,)

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
        current_record = dataset_persistence.get_dataframe_record(
            dataset=dataset,
            id_registro=id_registro,
        )

        previous_canonico = (
            ""
            if current_record.get("logradouro_canonico") is None
            else str(current_record.get("logradouro_canonico")).strip()
        )

        new_canonico = updates.get("logradouro_canonico")

        dataset = dataset_persistence.update_dataframe_record(
            dataset=dataset,
            id_registro=id_registro,
            updates=updates,
            usuario=usuario,
            note=note,
        )

        # Mantém o comportamento atual:
        # somente uma alteração real do logradouro canônico
        # gera/atualiza uma correção manual.
        if (
            "logradouro_canonico" in updates
            and new_canonico
            and str(new_canonico).strip() != previous_canonico
        ):
            AddressCorrectionService.apply_manual_correction(
                logradouro_original=current_record.get(
                    "logradouro",
                    "",
                ),
                logradouro_limpo=current_record.get(
                    "logradouro_limpo",
                    "",
                ),
                logradouro_canonico=str(new_canonico).strip(),
                usuario=usuario,
                note=note,
            )

        return dataset