# Generated by Django 2.2.16 on 2022-08-05 09:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0012_post_follow'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='follow',
        ),
    ]