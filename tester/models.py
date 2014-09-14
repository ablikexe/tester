from django.db import models

class tasks(models.Model):
    short = models.CharField(max_length=5, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    memlimit = models.IntegerField()
