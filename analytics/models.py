from django.db import models


class AddressCorrection(models.Model):

    STATUS_CHOICES = [
        ("PENDENTE", "Pendente"),
        ("APROVADO", "Aprovado"),
        ("REJEITADO", "Rejeitado"),
    ]

    ORIGEM_CHOICES = [
        ("MANUAL", "Manual"),
        ("AUTOMATICA", "Automática"),
    ]

    logradouro_original = models.TextField()

    logradouro_limpo = models.TextField(
        db_index=True
    )

    logradouro_canonico = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDENTE"
    )

    origem = models.CharField(
        max_length=20,
        choices=ORIGEM_CHOICES,
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

    def __str__(self):
        return f"{self.logradouro_limpo} -> {self.logradouro_canonico}"