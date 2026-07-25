from django.db import models


class AddressCorrection(models.Model):
	"""Armazena correções manuais de logradouros para uso futuro.

	Esta tabela será utilizada para persistir decisões manuais que deverão
	prevalecer sobre sugestões automáticas do pipeline.
	"""
	logradouro_original = models.TextField(blank=True)
	logradouro_limpo = models.TextField(db_index=True)
	logradouro_canonico = models.TextField()
	corrigido_manualmente = models.BooleanField(default=False)
	autor = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = "Correção de logradouro"
		verbose_name_plural = "Correções de logradouros"

	def __str__(self):
		return f"{self.logradouro_limpo} -> {self.logradouro_canonico}"
