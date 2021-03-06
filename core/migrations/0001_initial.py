# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-26 14:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Organisation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', models.SlugField(editable=False, max_length=255, unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
