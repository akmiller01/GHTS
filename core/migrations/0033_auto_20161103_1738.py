# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-03 17:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_auto_20161103_1736'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organisation',
            name='default',
        ),
        migrations.AddField(
            model_name='sector',
            name='default',
            field=models.BooleanField(default=False),
        ),
    ]
