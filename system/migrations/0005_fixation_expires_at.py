# Generated by Django 5.1.4 on 2025-02-23 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0004_alter_apartment_block_alter_apartment_builder_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fixation',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата истечения'),
        ),
    ]
