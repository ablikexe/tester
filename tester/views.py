# coding: utf8
from django.shortcuts import render, redirect
from django.contrib import messages
from tester.models import *
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from tester.settings import TASKS_DIR
from tester.forms import *
import os
import time


def show_tasks(request):
    return render(request, 'show_tasks.html', {'tasks': Task.objects.all()})


def show_task(request, short):
    tasks = Task.objects.filter(short=short)
    if len(tasks) == 0:
        messages.warning(request, 'Wrong task!')
        return redirect('/')
    return render(request, 'show_task.html', {'task': tasks[0]})


def download_test(request, test_id):
    test = Test.objects.filter(pk=test_id)
    if len(test) == 0:
        messages.warning('Unknown test!')
        return redirect('/')
    file_path = test.input
    response = HttpResponse(FileWrapper(open(file_path, 'r')), content_type='application/force-download')
    response['Content-Length'] = os.path.getsize(file_path)
    return response


def test(request):
    if request.method != 'POST':
        return redirect('/')
    short = request.POST['short']

    def path(s):
        return '%s/%s' % (short, s)

    with open('sol.cpp', 'w') as f:
        f.write(request.POST['code'])
    if os.system('g++ sol.cpp -o sol -std=c++11 -O2 -static -lm'):
        return render(request, 'results.html', { 'error': u'Błąd kompilacji' })
    res = []
    try:
        tests = open(path('tests'), 'r').readlines()
    except:
        try:
            os.system('python %s' % path('gen.py'))
            tests = open(path('tests'), 'r').readlines()
        except:
            return render(request, 'results.html', {'error': u'Błąd w trakcie generowania testów! (niepoprawny generator?)'})
    for test in tests:
        test_name, fin, fout = test.split()
        fin, fout = map(path, (fin, fout))
        beg = time.time()
        ex = os.system('./sol < %s > out' % fin)
        if ex:
            return render(request, 'results.html', {'error': u'Błąd wykonania!'})
        correct = open(fout, 'r').read().split()
        out = open('out').read().split()
        info = 'OK'
        for i in xrange(len(correct)):
            if i >= len(out):
                info = 'Oczekiwano %s, wczytano koniec pliku' % (correct[i])
                break
            elif out[i] != correct[i]:
                info = 'Oczekiwano %s, wczytano %s' % (correct[i], out[i])
        res.append((test_name, info, '%.3fs' % (time.time()-beg)))
    return render(request, 'results.html', {'results': res, 'short': short})


def add_task(request):
    if request.method != 'POST':
        return render(request, 'add_task.html', {'form': AddTaskForm()})
    form = AddTaskForm(request.POST)
    if not form.is_valid():
        return render(request, 'add_task.html', {'form': form})
    data = form.cleaned_data
    short = data['short']
    if Task.objects.filter(pk=short):
        messages.warning(request, u'Skrót nazwy zadania jest już używany!')
        return render(request, 'add_task.html', {'form': form})
    os.system('mkdir %s' % os.path.join(TASKS_DIR, short))
    with open(os.path.join(TASKS_DIR, short, 'info'), 'w') as f:
        f.write('Task name: %s\n' % data['name'])
        f.write('Memory limit: %d\n' % data['memlimit'])
    data['author'] = request.user
    task = Task(**data)
    task.save()
    messages.success(request, 'Task created!')
    return redirect('/')


def remove_task(request, short):
    t = Task.objects.filter(pk = short)
    if len(t) == 0:
        messages.warning(request, 'Wrong task!')
    else:
        os.system('rm -rf %s' % short)
        t[0].delete()
    return redirect('/')
