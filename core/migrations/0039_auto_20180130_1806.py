# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2018-01-30 18:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0038_auto_20180125_1414'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entry',
            name='refugee_facility_for_turkey',
        ),
        migrations.AddField(
            model_name='entry',
            name='facility',
            field=models.CharField(blank=True, choices=[('L', 'Facility for Refugees in Turkey'), ('E', 'EU Regional Trust Fund in response to the Syrian crisis'), ('G', 'Global Concessional Financing Facility')], max_length=1, null=True),
        ),
        migrations.AddField(
            model_name='organisation',
            name='disable_default_loan_sectors',
            field=models.BooleanField(default=False),
        ),
    ]
