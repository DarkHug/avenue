# Generated by Django 5.1.4 on 2025-03-04 19:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0013_fixationhistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='fixationhistory',
            name='fixation_id_reference',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='fixationhistory',
            name='fixation',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='history', to='system.fixation'),
        ),
    ]
