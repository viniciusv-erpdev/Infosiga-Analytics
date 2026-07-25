from django.contrib import admin

from .models import AddressCorrection


@admin.register(AddressCorrection)
class AddressCorrectionAdmin(admin.ModelAdmin):

    list_display = (
        "logradouro_limpo",
        "logradouro_canonico",
        "status",
        "origem",
        "autor",
        "created_at",
    )

    list_filter = (
        "status",
        "origem",
        "autor",
    )

    search_fields = (
        "logradouro_limpo",
        "logradouro_original",
        "logradouro_canonico",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )