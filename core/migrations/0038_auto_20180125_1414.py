# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-01-25 14:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0037_auto_20180124_2010'),
    ]

    operations = [
        migrations.AlterField(
            model_name='spreadsheet',
            name='year',
            field=models.IntegerField(choices=[(2016, 2016), (2017, '2017-2020'), (2, '2018-2020'), (1, 2017), (3, 2018), (4, '2019-2020')]),
        ),
    ]