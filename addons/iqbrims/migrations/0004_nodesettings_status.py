# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-05-13 08:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('addons_iqbrims', '0003_auto_20170713_1125'),
    ]

    operations = [
        migrations.AddField(
            model_name='nodesettings',
            name='status',
            field=models.TextField(blank=True, null=True),
        ),
    ]
