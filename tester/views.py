# coding: utf8
from django.shortcuts import render, redirect
from django.contrib import messages
from tester.models import *
import os, time

def show_tasks(request):
    return render(request, 'show_tasks.html', { 'tasks': tasks.objects.all() })

def show_task(request, short):
    task = tasks.objects.filter(short=short)
    if len(task) == 0:
        messages.warning(request, 'Wrong task!')
        return redirect('/')
    return render(request, 'show_task.html', { 'task': task[0] })

def download_test(request, short, test):
    return render(request, 'show_test.html', { 'test': open('%s/%s.in' % (short, test), 'r').read() })

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
            return render(request, 'results.html', { 'error': u'Błąd w trakcie generowania testów! (niepoprawny generator?)' })
    for test in tests:
        test_name, fin, fout = test.split()
        fin, fout = map(path, (fin, fout))
        beg = time.time()
        ex = os.system('./sol < %s > out' % fin)
        if ex:
            return render(request, 'results.html', { 'error': u'Błąd wykonania!' })
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
    return render(request, 'results.html', { 'results': res, 'short': short })

def add_task(request):
    if request.method != 'POST':
        return render(request, 'add_task.html')
    short = request.POST['short']
    if tasks.objects.filter(short=short):
        messages.warning(request, u'Skrót nazwy zadania jest już używany!')
        return render(request, 'add_task.html', {request: request})
    os.system('mkdir %s' % short)
    with open('%s/info' % short, 'w') as f:
        f.write('Task name: %s\n' % request.POST['name'].encode('utf-8'))
        f.write('Memory limit: %s\n' % request.POST['memlimit'])
    data = { x: request.POST[x] for x in ('short', 'name', 'description', 'memlimit') }
    task = tasks(**data)
    task.save()
    messages.success(request, 'Task created!')
    return redirect('/')
