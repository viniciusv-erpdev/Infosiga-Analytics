import pandas as pd
import re 
from difflib import SequenceMatcher
from rapidfuzz import process, fuzz

class DatasetSearchService:
    """
    Responsável pelas operações de pesquisa sobre
    os registros processados de um Dataset.
    """

    SEARCH_COLUMNS = (
        "logradouro",
        "logradouro_sugerido",
        "logradouro_canonico",
    )
    
    FUZZY_THRESHOLD = 78 
    FUZZY_LIMIT = 10
    
    @classmethod
    def filter_dataframe(cls, dataframe, query):
        """
        Filtra o DataFrame utilizando os campos de logradouro.

        A pesquisa é:
        - parcial;
        - case-insensitive;
        - sem alterar o DataFrame original;
        - utiliza fuzzy matching como fallback quando
        a busca literal não encontra resultados.
        """

        if dataframe is None:
            return dataframe

        query = str(query or "").strip()

        if not query:
            return dataframe.copy()

        available_columns = [
            column
            for column in cls.SEARCH_COLUMNS
            if column in dataframe.columns
        ]

        if not available_columns:
            return dataframe.iloc[0:0].copy()

    # ==========================================================
    # 1. BUSCA LITERAL
    # ==========================================================

        mask = pd.Series(
            False,
            index=dataframe.index,
        )

        for column in available_columns:
            values = (
                dataframe[column]
                .fillna("")
                .astype(str)
            )

            mask |= values.str.contains(
                query,
                case=False,
                regex=False,
                na=False,
            )

        literal_results = dataframe.loc[mask].copy()

        if not literal_results.empty:
            return literal_results

    # ==========================================================
    # 2. FUZZY MATCHING
    # ==========================================================

        if len(query) < 3:
            return dataframe.iloc[0:0].copy()

        fuzzy_mask = pd.Series(
            False,
            index=dataframe.index,
        )

        for column in (
            "logradouro_canonico",
            "logradouro_sugerido",
            "logradouro",
        ):
            if column not in dataframe.columns:
                continue

            values = (
                dataframe[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            unique_values = (
                values[
                    values != ""
                ]
                .drop_duplicates()
                .tolist()
            )

            if not unique_values:
                continue

            matches = process.extract(
                query,
                unique_values,
                scorer=fuzz.WRatio,
                limit=cls.FUZZY_LIMIT,
                score_cutoff=cls.FUZZY_THRESHOLD,
            )

            matched_values = {
                match[0]
                for match in matches
            }

            if not matched_values:
                continue

            fuzzy_mask |= values.isin(
                matched_values
            )

        return dataframe.loc[fuzzy_mask].copy()
    
    @classmethod
    def get_suggestions(cls, dataframe, query, limit=10):
        """
        Retorna sugestões distintas de logradouro.

        A busca possui duas etapas:

        1. Correspondência textual parcial;
        2. Correspondência aproximada por similaridade.

        A prioridade dos campos permanece:

        1. logradouro_canonico
        2. logradouro_sugerido
        3. logradouro
        """

        if dataframe is None:
            return []

        query = str(query or "").strip()

        if len(query) < 2:
            return []

        suggestions = []

        # ---------------------------------------------------------
        # 1. BUSCA LITERAL
        # ---------------------------------------------------------

        for column in (
            "logradouro_canonico",
            "logradouro_sugerido",
            "logradouro",
        ):
            if column not in dataframe.columns:
                continue

            values = (
                dataframe[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            values = values[
                values != ""
            ]

            matching_values = values[
                values.str.contains(
                    query,
                    case=False,
                    regex=False,
                    na=False,
                )
            ]

            for value in matching_values:
                if value not in suggestions:
                    suggestions.append(value)

                if len(suggestions) >= limit:
                    return suggestions

        # ---------------------------------------------------------
        # 2. BUSCA APROXIMADA
        # ---------------------------------------------------------

        candidates = []

        for column in (
            "logradouro_canonico",
            "logradouro_sugerido",
            "logradouro",
        ):
            if column not in dataframe.columns:
                continue

            values = (
                dataframe[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            values = values[
                values != ""
            ]

            for value in values.unique():
                score = cls._similarity_score(
                    query,
                    value,
                )

                candidates.append(
                    (
                        score,
                        value,
                    )
                )

        # Ordena pela maior similaridade.
        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        # Adiciona somente valores que ultrapassarem
        # o limite mínimo de similaridade.
        MIN_SIMILARITY = 0.55

        for score, value in candidates:

            if score < MIN_SIMILARITY:
                break

            if value not in suggestions:
                suggestions.append(value)

            if len(suggestions) >= limit:
                break

        return suggestions

    @classmethod
    def get_fuzzy_suggestions(cls, dataframe, query, limit=None):
        """
        Retorna sugestões aproximadas de logradouro utilizando
        fuzzy matching.

        A busca prioriza:
        1. logradouro_canonico
        2. logradouro_sugerido
        3. logradouro

        Retorna uma lista de dicionários contendo:
        - value: valor sugerido
        - score: grau de similaridade
        - source: coluna de origem
        """

        if dataframe is None:
            return []

        query = str(query or "").strip()

        if len(query) < 3:
            return []

        if limit is None:
            limit = cls.FUZZY_LIMIT

        suggestions = []
        seen = set()

        for column in (
            "logradouro_canonico",
            "logradouro_sugerido",
            "logradouro",
        ):
            if column not in dataframe.columns:
                continue

            values = (
                dataframe[column]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            values = values[
                values != ""
            ]

            unique_values = values.drop_duplicates().tolist()

            if not unique_values:
                continue

            matches = process.extract(
                query,
                unique_values,
                scorer=fuzz.WRatio,
                limit=limit,
                score_cutoff=cls.FUZZY_THRESHOLD,
            )

            for value, score, _ in matches:

                normalized_value = value.casefold()

                if normalized_value in seen:
                    continue

                seen.add(normalized_value)

                suggestions.append({
                    "value": value,
                    "score": round(score, 2),
                    "source": column,
                })

        suggestions.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return suggestions[:limit]
    
    @staticmethod
    def _similarity_score(query, value):
        """
        Calcula a similaridade entre uma consulta e um logradouro.

        A comparação é feita tanto com o valor completo quanto
        individualmente com cada palavra do logradouro.

        Retorna a maior similaridade encontrada.
        """

        query = str(query or "").strip().lower()
        value = str(value or "").strip().lower()

        if not query or not value:
            return 0.0

        # Comparação com o valor completo.
        best_score = SequenceMatcher(
            None,
            query,
            value,
        ).ratio()

        # Remove pontuação e separa o logradouro em palavras.
        tokens = re.findall(
            r"\b\w+\b",
            value,
        )

        # Compara a consulta com cada palavra.
        for token in tokens:
            score = SequenceMatcher(
                None,
                query,
                token,
            ).ratio()

            best_score = max(
                best_score,
                score,
            )

        return best_score