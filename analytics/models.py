from django.db import models
from django.conf import settings

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
        db_index=True,
        unique=True
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


class CorrectionAudit(models.Model):
    """Auditoria de alterações em correções de logradouro.

    Mantém histórico imutável das alterações realizadas sobre
    `AddressCorrection`. A FK para `AddressCorrection` é opcional e usa
    `SET_NULL` para preservar o histórico mesmo se o registro for removido.
    """
    correction = models.ForeignKey(
        "analytics.AddressCorrection",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audits",
    )

    logradouro_limpo = models.TextField(db_index=True, blank=True)

    field_name = models.CharField(max_length=100, blank=True)
    previous_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    previous_status = models.CharField(max_length=20, null=True, blank=True)
    new_status = models.CharField(max_length=20, null=True, blank=True)

    autor = models.CharField(max_length=255, blank=True)
    origin = models.CharField(max_length=50, blank=True)
    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Audit {self.logradouro_limpo} @ {self.created_at.isoformat()}"

class Dataset(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="datasets",
    )

    nome_original = models.CharField(
        max_length=255
    )

    arquivo = models.FileField(
        upload_to="datasets/"
    )

    quantidade_registros = models.PositiveIntegerField(
        default=0
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    atualizado_em = models.DateTimeField(
        auto_now=True
    )

    resultado_processado = models.FileField(
        upload_to="datasets/processed/",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.nome_original