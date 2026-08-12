from analytics.persistence import datasets as dataset_persistence


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

        return dataframe[
            existing_priority_columns + remaining_columns
        ]