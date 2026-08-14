from pathlib import Path
import pandas as pd
from analytics.models import Dataset
from analytics.models import DatasetRecordAudit

def save_dataframe_as_parquet(dataframe: pd.DataFrame, path: str | Path) -> Path:
    """
    Salva um DataFrame em formato Parquet.

    Retorna o caminho do arquivo criado.
    """
    if dataframe is None:
        raise ValueError("dataframe não pode ser None")

    path = Path(path)

    path.parent.mkdir(parents=True, exist_ok=True)

    dataframe.to_parquet(
        path,
        index=False,
    )

    return path


def load_dataframe_from_parquet(path: str | Path) -> pd.DataFrame:
    """
    Carrega um arquivo Parquet e retorna um DataFrame.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo Parquet não encontrado: {path}"
        )

    return pd.read_parquet(path)

def create_dataset(
    usuario,
    nome_original: str,
    arquivo,
    quantidade_registros: int,
) -> Dataset:
    """
    Cria e persiste um Dataset associado a um usuário.
    """

    if usuario is None:
        raise ValueError("usuario é obrigatório")

    if arquivo is None:
        raise ValueError("arquivo é obrigatório")

    if not nome_original:
        raise ValueError("nome_original é obrigatório")

    if quantidade_registros < 0:
        raise ValueError("quantidade_registros não pode ser negativo")

    return Dataset.objects.create(
        usuario=usuario,
        nome_original=nome_original,
        arquivo=arquivo,
        quantidade_registros=quantidade_registros,
    )

def list_datasets_for_user(usuario):
    return (
        Dataset.objects
        .filter(usuario=usuario)
        .order_by("-criado_em")
    )


def get_dataset_for_user(dataset_id, usuario):
    return (
        Dataset.objects
        .filter(
            id=dataset_id,
            usuario=usuario,
        )
        .first()
    )

def save_processed_dataframe(
    dataset: Dataset,
    dataframe: pd.DataFrame,
) -> Dataset:
    """
    Salva o DataFrame processado em Parquet e associa
    o arquivo resultante ao Dataset.
    """
    if dataset is None:
        raise ValueError("dataset não pode ser None")

    if dataframe is None:
        raise ValueError("dataframe não pode ser None")

    nome_original = Path(dataset.nome_original).stem
    nome_arquivo = f"{nome_original}_processado.parquet"

    caminho = (
        Path(dataset.arquivo.storage.location)
        / "datasets"
        / "processed"
        / nome_arquivo
    )

    save_dataframe_as_parquet(
        dataframe=dataframe,
        path=caminho,
    )

    caminho_relativo = (
        Path("datasets")
        / "processed"
        / nome_arquivo
    ).as_posix()

    dataset.resultado_processado.name = caminho_relativo

    dataset.save(
        update_fields=[
            "resultado_processado",
            "atualizado_em",
        ]
    )

    return dataset

def load_processed_dataframe(dataset: Dataset) -> pd.DataFrame:
    """
    Carrega o DataFrame processado associado a um Dataset.
    """

    if dataset is None:
        raise ValueError("dataset não pode ser None")

    if not dataset.resultado_processado:
        raise ValueError(
            "O dataset ainda não possui resultado processado."
        )

    return load_dataframe_from_parquet(
        dataset.resultado_processado.path
    )

def list_datasets_for_user(usuario):
    return (
        Dataset.objects
        .filter(usuario=usuario)
        .order_by("-criado_em")
    )

def update_dataframe_record(
    dataset: Dataset,
    id_registro,
    updates: dict,
    usuario,
    note: str = "",
) -> Dataset:
    """
    Atualiza campos editáveis de um registro no Parquet e registra
    cada alteração no histórico de auditoria.

    O campo `logradouro` original não pode ser alterado.
    """

    if dataset is None:
        raise ValueError("dataset é obrigatório")

    if usuario is None:
        raise ValueError("usuario é obrigatório")

    if not updates:
        raise ValueError("Nenhuma alteração foi informada")

    if not dataset.resultado_processado:
        raise ValueError(
            "O dataset ainda não possui resultado processado."
        )

    dataframe = load_processed_dataframe(dataset)

    if "id_registro" not in dataframe.columns:
        raise ValueError(
            "O dataset não possui a coluna id_registro."
        )

    id_registro = str(id_registro)

    mask = (
        dataframe["id_registro"].astype(str) == id_registro
    )

    if not mask.any():
        raise ValueError(
            f"Registro não encontrado: {id_registro}"
        )

    editable_field_types = {
        "numero_logradouro": "numeric",
        "logradouro_canonico": "text",
    }

    invalid_fields = (
    set(updates.keys()) - set(editable_field_types.keys())
    )

    if invalid_fields:
        raise ValueError(
            f"Campos não editáveis: {', '.join(invalid_fields)}"
        )

    row_index = dataframe.index[mask][0]

    changes = []

    for field_name, new_value in updates.items():

        if field_name not in dataframe.columns:
            raise ValueError(
                f"Campo inexistente no dataset: {field_name}"
            )

        field_type = editable_field_types[field_name]

        if field_type == "numeric":
            try:
                if new_value in (None, ""):
                    converted_value = None
                else:
                    converted_value = float(new_value)
            except (TypeError, ValueError):
                raise ValueError(
                    f"O campo {field_name} deve conter um valor numérico."
                )
        else:
            converted_value = (
                ""
                if new_value is None
                else str(new_value).strip()
            )    

        previous_value = dataframe.at[
            row_index,
            field_name,
        ]

        previous_str = (
            ""
            if pd.isna(previous_value)
            else str(previous_value)
        )

        new_str = (
            ""
            if converted_value is None
            else str(converted_value)
        )

        # Não registra auditoria quando não houve mudança real.
        if previous_str == new_str:
            continue

        changes.append(
            {
                "field_name": field_name,
                "previous_value": previous_str,
                "new_value": new_str,
            }
        )

        dataframe.at[
            row_index,
            field_name,
        ] = converted_value

    if not changes:
        return dataset

    # Salva o Parquet atualizado.
    save_processed_dataframe(
        dataset=dataset,
        dataframe=dataframe,
    )

    # Registra cada alteração realizada.
    for change in changes:
        DatasetRecordAudit.objects.create(
            dataset=dataset,
            id_registro=id_registro,
            field_name=change["field_name"],
            previous_value=change["previous_value"],
            new_value=change["new_value"],
            usuario=usuario,
            note=note,
        )

    return dataset

def delete_dataset(dataset: Dataset) -> None:

    if dataset is None:
        raise ValueError("dataset não pode ser None")

    if dataset.arquivo:
        dataset.arquivo.delete(save=False)

    if dataset.resultado_processado:
        dataset.resultado_processado.delete(save=False)

    dataset.delete()

#Função de manutenção para remover datasets órfãos (sem arquivo associado)
def cleanup_orphaned_datasets():

    removed = 0

    for dataset in Dataset.objects.all():

        arquivo_existe = (
            not dataset.arquivo
            or dataset.arquivo.storage.exists(
                dataset.arquivo.name
            )
        )

        resultado_existe = (
            not dataset.resultado_processado
            or dataset.resultado_processado.storage.exists(
                dataset.resultado_processado.name
            )
        )

        if not arquivo_existe or not resultado_existe:
            dataset.delete()
            removed += 1

    return removed

