# Generated by Django 3.2.4 on 2021-06-23 23:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('memetext', '0011_testannotation_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='CrawledRedditPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('post_id', models.CharField(max_length=12, unique=True)),
                ('post_url', models.CharField(max_length=255)),
                ('image_hash', models.CharField(max_length=255)),
                ('s3_image', models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='memetext.s3image')),
            ],
        ),
    ]