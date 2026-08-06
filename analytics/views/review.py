import json
from django.shortcuts import render

from analytics.persistence.corrections import get_correction_by_limpo


def get_preview_source(session):
    """Ponto de abstração para obter os dados da fonte da Central de Revisão.

    Atualmente retorna `request.session['preview_data']`. Futuramente
    essa função pode ser substituída para obter dados de uma API/DB
    sem alterar a view nem o frontend.
    """
    return session.get("preview_data")


def _normalize_row_maps(preview):
    """Constrói listas de dicionários unificados a partir da estrutura de
    `preview_data` existente (rows, regularization_rows, audit_rows).
    """
    if not preview:
        return []

    rows = preview.get("rows", [])
    columns = preview.get("columns", [])
    reg_cols = preview.get("regularization_columns", [])
    reg_rows = preview.get("regularization_rows", [])
    audit_cols = preview.get("audit_columns", [])
    audit_rows = preview.get("audit_rows", [])

    max_len = max(len(rows), len(reg_rows), len(audit_rows))
    unified = []

    for i in range(max_len):
        rec = {}
        # base columns
        if i < len(rows):
            for idx, col in enumerate(columns):
                try:
                    rec[col] = rows[i][idx]
                except Exception:
                    rec[col] = ""

        # regularization
        if i < len(reg_rows):
            for idx, col in enumerate(reg_cols):
                try:
                    rec[col] = reg_rows[i][idx]
                except Exception:
                    rec[col] = ""

        # audit
        if i < len(audit_rows):
            for idx, col in enumerate(audit_cols):
                try:
                    rec[col] = audit_rows[i][idx]
                except Exception:
                    rec[col] = ""

        # normaliza nomes esperados
        registro = {
            "logradouro": rec.get("Logradouro original") or rec.get("logradouro") or "",
            "logradouro_normalizado": rec.get("Logradouro normalizado") or rec.get("logradouro_normalizado") or "",
            "logradouro_limpo": rec.get("Logradouro limpo") or rec.get("logradouro_limpo") or "",
            "logradouro_canonico": rec.get("Logradouro canônico") or rec.get("logradouro_canonico") or "",
            "similaridade": rec.get("Similaridade (%)") or rec.get("similaridade") or "",
            "frequencia_grupo": rec.get("Frequência do grupo") or rec.get("frequencia_grupo") or 0,
        }

        # campos opcionais: confianca_matching, correcao_manual_aplicada
        if "confianca_matching" in rec:
            registro["confianca_matching"] = rec.get("confianca_matching")

        if "correcao_manual_aplicada" in rec:
            registro["correcao_manual_aplicada"] = rec.get("correcao_manual_aplicada")

        # obter status de correção manual existente (somente leitura)
        status = ""
        correcao_nome = ""
        if registro["logradouro_limpo"]:
            cor = get_correction_by_limpo(registro["logradouro_limpo"])
            if cor is not None:
                status = getattr(cor, "status", "") or ""
                correcao_nome = getattr(cor, "logradouro_canonico", "") or ""

        registro["status_revisao"] = status
        registro["correcao_manual_nome"] = correcao_nome

        # latitude/longitude não disponíveis na preview atual — placeholder
        registro["latitude"] = rec.get("latitude") or rec.get("Latitude") or ""
        registro["longitude"] = rec.get("longitude") or rec.get("Longitude") or ""

        unified.append(registro)

    # ordenação: priorizar MEDIA/BAIXA em `confianca_matching` quando disponível
    def _sort_key(r):
        cm = r.get("confianca_matching")
        if cm in ("MEDIA", "BAIXA"):
            return (0,)
        if cm == "MANUAL":
            return (2,)
        return (1,)

    if any("confianca_matching" in r for r in unified):
        unified.sort(key=_sort_key)

    return unified


def review_list(request):
    preview = get_preview_source(request.session) or {}
    records = _normalize_row_maps(preview)

    context = {
        "records": records,
    }

    return render(request, "analytics/review_list.html", context)
