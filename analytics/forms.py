import os

from django import forms
from django.core.exceptions import ValidationError


class UploadFileForm(forms.Form):
    arquivo = forms.FileField(
        label="Selecione um arquivo",
        required=True,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": ".csv,.xlsx,.xls,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv",
            }
        ),
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data.get("arquivo")

        if arquivo is None:
            return arquivo

        ext = os.path.splitext(arquivo.name)[1].lower()
        if ext not in {".csv", ".xls", ".xlsx"}:
            raise ValidationError("Somente arquivos CSV ou Excel (.xls, .xlsx) são permitidos.")

        return arquivo
