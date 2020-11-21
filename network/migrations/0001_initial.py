# Generated by Django 3.1.2 on 2020-11-21 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('deviceName', models.CharField(max_length=10, unique=True)),
                ('deviceType', models.CharField(max_length=20)),
                ('connectedDevices', models.ManyToManyField(blank=True, to='network.Device')),
            ],
        ),
    ]
