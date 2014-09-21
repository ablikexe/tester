from django.contrib.auth.models import *

class Task(models.Model):
    name = models.CharField(max_length=100)
    clear_name = models.CharField(max_length=100)
    memlimit = models.IntegerField()
    description = models.TextField()
    author = models.ForeignKey(User)

    def __unicode__(self):
        return self.name


class Test(models.Model):
    task = models.ForeignKey(Task)
    name = models.CharField(max_length=20)
    timelimit = models.IntegerField()
    points = models.IntegerField()


UNKNOWN = 0
PROCESSING = 1
PROCESSED = 2
COMPILATION_ERROR = 3


class Solution(models.Model):
    task = models.ForeignKey(Task)
    user = models.ForeignKey(User)
    permissions = models.TextField()
    code = models.TextField()
    status = models.IntegerField(default=UNKNOWN)
    date = models.DateTimeField()
    results = models.TextField()
    points = models.IntegerField(default=0)


class Query(models.Model):
    solution = models.ForeignKey(Solution)
