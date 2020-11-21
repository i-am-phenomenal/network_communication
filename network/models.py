from django.db import models

class Device(models.Model): 
    id = models.AutoField(primary_key=True)
    deviceName =models.CharField(max_length=10, unique=True)
    deviceType= models.CharField(max_length=20)
    connectedDevices = models.ManyToManyField("self", blank=True, symmetrical=False)
    deviceStrength = models.PositiveIntegerField(default=5)

