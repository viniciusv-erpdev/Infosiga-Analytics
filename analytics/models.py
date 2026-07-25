from django.db import models


class AddressCorrection(models.Model):
    logradouro_original = models.TextField()

    logradouro_limpo = models.TextField(
        db_index=True
    )
    logradouro_canonico = models.TextField()
    status = models.CharField(
        max_length=20,
        default="PENDENTE"
    )
    origem = models.CharField(
        max_length=20,
        default="MANUAL"
    )
    score_similaridade = models.FloatField(
        null=True,
        blank=True
    )
    autor = models.CharField(
        max_length=255,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )