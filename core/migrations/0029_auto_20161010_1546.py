# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-10 15:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_auto_20161007_1653'),
    ]

    operations = [
        migrations.AlterField(
            model_name='currency',
            name='symbol',
            field=models.CharField(max_length=10),
        ),
    ]
