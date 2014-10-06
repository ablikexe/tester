from django.contrib.auth.models import *
from django.utils import timezone

class Task(models.Model):
    name = models.CharField(max_length=100)
    clear_name = models.CharField(max_length=100)
    memlimit = models.IntegerField()
    description = models.TextField()
    author = models.ForeignKey(User)
    active = models.BooleanField(default=True)
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return self.name

class Test(models.Model):
    task = models.ForeignKey(Task, db_index=True)
    name = models.CharField(max_length=20)
    timelimit = models.IntegerField()
    points = models.IntegerField()

UNKNOWN = 0
PROCESSING = 1
COMPILATION_ERROR = 3
CORRECT = 2
WRONG_ANSWER = 4
TIME_LIMIT_EXCEEDED = 5
RUNTIME_ERROR = 6

PROCESSED_STATUSES = [2, 4, 5, 6]

class Solution(models.Model):
    task = models.ForeignKey(Task, db_index=True)
    user = models.ForeignKey(User)
    description = models.TextField(default='')
    published = models.BooleanField(default=False)
    need_help = models.BooleanField(default=False)
    code = models.TextField()
    status = models.IntegerField(default=UNKNOWN)
    date = models.DateTimeField(default=timezone.now)
    results = models.TextField()
    points = models.IntegerField(default=0)

class Query(models.Model):
    solution = models.ForeignKey(Solution)

class UserData(models.Model):
    user = models.OneToOneField(User)
    ranking = models.BooleanField(default=1)

class Comment(models.Model):
    content = models.TextField()
    author = models.ForeignKey(User)
    date = models.DateTimeField(default=timezone.now)
    solution = models.ForeignKey(Solution, db_index=True, null=True)
    task = models.ForeignKey(Task, db_index=True, null=True)

class Notification(models.Model):
    to = models.ForeignKey(User)
    read = models.BooleanField(default=False)
    content = models.TextField()
