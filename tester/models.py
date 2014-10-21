#coding: utf8
from django.contrib.auth.models import *
from django.utils import timezone

class Task(models.Model):
    name = models.CharField(max_length=100)
    clear_name = models.CharField(max_length=100)
    memlimit = models.IntegerField()
    description = models.TextField()
    author = models.ForeignKey(User)
    active = models.BooleanField(default=False)
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField(default=timezone.now)
    foreign = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

class Test(models.Model):
    task = models.ForeignKey(Task, db_index=True)
    name = models.CharField(max_length=20)
    timelimit = models.IntegerField()
    points = models.IntegerField()

UNKNOWN = 0
PROCESSING = 1
CORRECT = 2
COMPILATION_ERROR = 3
WRONG_ANSWER = 4
TIME_LIMIT_EXCEEDED = 5
RUNTIME_ERROR = 6

STATUS_DESCRIPTION = ['Oczekiwanie na ocenę', 'W trakcie oceniania', 'OK', 'Błąd kompilacji', 'Zła odpowiedź', 'Przekroczono limit czasu', 'Błąd wykonania']

LANGUAGES = {
    'c++': 'g++ sol.cpp -o sol -O2 -lm -static -std=c++11',
    'pas': 'ppcx64 -O2 -XS -Xt sol.cpp'
}

class Solution(models.Model):
    task = models.ForeignKey(Task, db_index=True)
    user = models.ForeignKey(User)
    description = models.TextField()
    published = models.BooleanField(default=False)
    need_help = models.BooleanField(default=False)
    language = models.CharField(max_length=3, default='c++')
    code = models.TextField()
    status = models.IntegerField(default=UNKNOWN)
    compilation_output = models.TextField(default='')
    date = models.DateTimeField(default=timezone.now)
    points = models.IntegerField(default=0)

class Result(models.Model):
    solution = models.ForeignKey(Solution, db_index=True)
    test = models.ForeignKey(Test)
    status = models.IntegerField()
    status_description = models.TextField(default='')
    time = models.IntegerField()
    points = models.IntegerField()

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
