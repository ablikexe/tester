# coding: utf8
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import *
from django.contrib.auth.decorators import login_required
from tester.models import *
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from tester.settings import TASKS_DIR
from tester.forms import *
import os
import time
import string


def clear(name):
    allowed = string.ascii_lowercase + string.digits + '-'
    name = name.lower().replace(' ', '-')
    polish = [u'ąćęłńóśźż',
              u'acelnoszz']
    for a, b in zip(*polish):
        name = name.replace(a, b)
    return ''.join(filter(allowed.__contains__, name))


def show_tasks(request):
    return render(request, 'show_tasks.html', {'tasks': Task.objects.all()})


def show_task(request, clear_name):
    tasks = Task.objects.filter(clear_name=clear_name)
    if len(tasks) == 0:
        messages.warning(request, 'Nieznane zadanie!')
        return redirect('/')
    return render(request, 'show_task.html', {'task': tasks[0]})


def login(request):

    if request.method != 'POST':
        return render(request, 'login.html', {'form': LoginForm()})

    form = LoginForm(request.POST)
    if not form.is_valid():
        return render(request, 'login.html', {'form': form})

    user = authenticate(username=form['username'], password=form['password'])
    if user is None:
        messages.warning(request, 'Nieprawidłowa nazwa użytkownika lub hasło!')
        return render(request, 'login.html', {'form': form})
    if not user.is_active:
        messages.warning(request, 'To konto jest nieaktywne!')
        return render(request, 'login.html', {'form': form})
    login(request, user)
    messages.success(request, 'Zalogowano pomyślnie!')
    return redirect('/')

@login_required
def download_test(request, test_id):
    test = Test.objects.filter(pk=test_id)
    if len(test) == 0:
        messages.warning('Nieznany test!')
        return redirect('/')
    file_path = test.input
    response = HttpResponse(FileWrapper(open(file_path, 'r')), content_type='application/force-download')
    response['Content-Length'] = os.path.getsize(file_path)
    return response

@login_required
def add_task(request):

    if request.method != 'POST':
        return render(request, 'add_task.html', {'form': AddTaskForm()})

    print request.FILES
    form = AddTaskForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'add_task.html', {'form': form})

    data = form.cleaned_data
    clean_name = clear(data['name'])

    if Task.objects.filter(clean_name=clean_name):
        messages.warning(request, u'Zadanie o tej nazwie już istnieje!')
        return render(request, 'add_task.html', {'form': form})

    os.system('mkdir %s' % os.path.join(TASKS_DIR, clean_name))
    with open(os.path.join(TASKS_DIR, clean_name, 'info'), 'w') as f:
        f.write('Nazwa zadania: %s\n' % data['name'].encode('utf-8'))
        f.write('Limit pamięci: %d\n' % data['memlimit'])
        f.write('Autor: %s\n' % request.user)
    print request.user
    data['author'] = request.user

    print request.FILES

    task = Task(**data)
    task.save()
    messages.success(request, u'Zadanie utworzone pomyślnie!')
    return redirect('/')

@login_required
def remove_task(request, task_id):
    t = Task.objects.filter(pk=task_id)
    if len(t) == 0:
        messages.warning(request, u'Nieznane zadanie!')
    else:
        os.system('rm -rf %s' % t.clear_name)
        t[0].delete()
    return redirect('/')
