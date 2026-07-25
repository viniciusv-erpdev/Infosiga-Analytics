from django.contrib import admin

from .models import AddressCorrection


@admin.register(AddressCorrection)
class AddressCorrectionAdmin(admin.ModelAdmin):
	list_display = ("logradouro_limpo", "logradouro_canonico", "corrigido_manualmente", "autor", "created_at")
	list_filter = ("corrigido_manualmente", "autor")
	search_fields = ("logradouro_limpo", "logradouro_original", "logradouro_canonico")
	readonly_fields = ("created_at", "updated_at")
