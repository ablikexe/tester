from django.contrib.auth.models import *


class Task(models.Model):
    name = models.CharField(max_length=100)
    clean_name = models.CharField(max_length=100)
    memlimit = models.IntegerField()
    description = models.TextField()
    author_solution = models.TextField()
    generator = models.TextField(null=True)
    checker = models.TextField(null=True)
    author = models.ForeignKey(User)

    def __unicode__(self):
        return self.name


class Test(models.Model):
    task = models.ForeignKey(Task)
    input = models.TextField()
    output = models.TextField()
    timelimit = models.IntegerField()
    points = models.IntegerField()


class Solution(models.Model):
    task = models.ForeignKey(Task)
    user = models.ForeignKey(User)
    permissions = models.TextField()
    code = models.TextField()
    results = models.TextField()
