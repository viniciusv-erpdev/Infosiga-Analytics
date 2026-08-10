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
    def list_for_user(usuario):
        return dataset_persistence.list_datasets_for_user(
            usuario
        )

    @staticmethod
    def get_for_user(dataset_id, usuario):
        return dataset_persistence.get_dataset_for_user(
            dataset_id=dataset_id,
            usuario=usuario,
        )