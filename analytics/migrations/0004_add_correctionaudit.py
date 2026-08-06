# Generated migration for adding CorrectionAudit model
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0003_alter_addresscorrection_origem_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorrectionAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logradouro_limpo', models.TextField(blank=True, db_index=True)),
                ('field_name', models.CharField(blank=True, max_length=100)),
                ('previous_value', models.TextField(blank=True, null=True)),
                ('new_value', models.TextField(blank=True, null=True)),
                ('previous_status', models.CharField(blank=True, max_length=20, null=True)),
                ('new_status', models.CharField(blank=True, max_length=20, null=True)),
                ('autor', models.CharField(blank=True, max_length=255)),
                ('origin', models.CharField(blank=True, max_length=50)),
                ('note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('correction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audits', to='analytics.addresscorrection')),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
        migrations.AddIndex(
            model_name='correctionaudit',
            index=models.Index(fields=['correction'], name='analytics_correc_corre_123456_idx'),
        ),
        migrations.AddIndex(
            model_name='correctionaudit',
            index=models.Index(fields=['logradouro_limpo'], name='analytics_correc_logr_123456_idx'),
        ),
    ]
