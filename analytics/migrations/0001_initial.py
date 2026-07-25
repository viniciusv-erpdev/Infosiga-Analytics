from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AddressCorrection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logradouro_original', models.TextField(blank=True)),
                ('logradouro_limpo', models.TextField(db_index=True)),
                ('logradouro_canonico', models.TextField()),
                ('corrigido_manualmente', models.BooleanField(default=False)),
                ('autor', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Correção de logradouro',
                'verbose_name_plural': 'Correções de logradouros',
            },
        ),
    ]
