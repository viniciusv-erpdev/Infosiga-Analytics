from pathlib import Path
import pandas as pd
from analytics.models import Dataset

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