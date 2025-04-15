# Generated by Django 4.2.20 on 2025-04-15 11:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='classification',
            field=models.CharField(blank=True, help_text='Тип содержимого страницы: сертификат, титульный лист и т.п.', max_length=100, null=True),
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('characteristics', models.JSONField(default=dict)),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='materials', to='documents.page')),
            ],
        ),
    ]
