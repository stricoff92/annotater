# Generated by Django 3.2.4 on 2021-06-19 15:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('memetext', '0008_alter_controlannotation_s3_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotationbatch',
            name='batch_message_expanded',
            field=models.TextField(blank=True, default=''),
        ),
    ]
