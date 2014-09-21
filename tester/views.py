# coding: utf8
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from tester.models import *
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.forms.formsets import formset_factory
from tester.settings import TASKS_DIR
from tester.forms import *
from django.utils import timezone
from django.utils.html import *
from threading import Thread, Event
import time
import os
import json
import string
import subprocess as sp


is_admin = lambda user: user.is_staff
logged_in = lambda user: user.is_authenticated() and user.is_active


def judge(sol):
    print 'Judging!'
    sol.status = PROCESSING
    with open('sol.cpp', 'w') as f:
        f.write(sol.code)
    p = sp.Popen(['g++', 'sol.cpp', '-o', 'sol', '-static', '-lm', '-O2', '-std=c++11'], stderr=sp.PIPE)   # albo c++0x
    _, err = p.communicate()
    if p.returncode != 0:
        sol.status = COMPILATION_ERROR
        sol.save()
        return

    task = sol.task
    tests = Test.objects.filter(task=task)
    res, total = [], 0
    for test in tests:
        test_path = os.path.join(TASKS_DIR, task.clear_name, 'tests', test.name)
        beg = time.time()
        p = sp.Popen('./sol', stdin=open('%s.in' % test_path, 'r'), stdout=open('out', 'w'))
        p.wait()
        t = 1000*(time.time() - beg)
        if t > test.timelimit:
            status, points = u'Przekroczono limit czasu', 0
        elif p.returncode != 0:
            status, points = u'Błąd wykonania', 0
        else:
            try:
                sp.check_call(['diff', '-wB', 'out', '%s.out' % test_path])
                status, points = u'OK', test.points
            except sp.CalledProcessError:
                status, points = u'Zła odpowiedź', 0
        res.append((test.name, status, '%.3fs/%.3fs' % (0.001*t, 0.001*test.timelimit), '%d/%d' % (points, test.points)))
        total += points

    sol.status = PROCESSED
    sol.results = json.dumps(res)
    sol.points = total
    sol.save()


taskevent = Event ()
def testall():
    while True:
        q = Query.objects.all()
        if len(q) == 0:
            print ('no more solutions to check')
            taskevent.clear()
            taskevent.wait ()
        else:
            print ('checking solution %s %s %s' % (q[0].solution.task.name, q[0].solution.user.username, q[0].solution.date))
            judge(q[0].solution)
            q[0].delete ()

testthread = Thread(name='testing', target=testall)
testthread.daemon = True


def clear(name):
    allowed = string.ascii_lowercase + string.digits + '-'
    name = name.lower().replace(' ', '-')
    replace = [u'ąćęłńóśźż',
               u'acelnoszz']
    for a, b in zip(*replace):
        name = name.replace(a, b)
    return ''.join(filter(allowed.__contains__, name))


def save_file(file, path):
    with open(path, 'wb+') as f:
        for chunk in file.chunks():
            f.write(chunk)


def show_tasks(request):
    return render(request, 'show_tasks.html', {'tasks': Task.objects.all()})


def show_task(request, clear_name):
    tasks = Task.objects.filter(clear_name=clear_name)
    if len(tasks) == 0:
        messages.warning(request, 'Nieznane zadanie!')
        return redirect('/')
    return render(request, 'show_task.html', {'task': tasks[0], 'task_id': tasks[0].pk})


def signup(request):
    if request.method != 'POST':
        return render(request, 'signup.html', {'form': SignupForm()})

    form = SignupForm(request.POST)
    if not form.is_valid():
        return render(request, 'signup.html', {'form': form})

    data = form.cleaned_data
    try:
        User.objects.get(username=data['username'])
        form.add_error('username', 'Istnieje już taki użytkownik')
        return render(request, 'signup.html', {'form': form})
    except:
        pass

    if data['pass1'] != data['pass2']:
        form.add_error('pass1', 'Hasła nie zgadzają się')
        return render(request, 'signup.html', {'form': form})

    User.objects.create_user(data['username'], data['email'], data['pass1'])
    messages.success(request, "Użytkownik utworzony pomyślnie")
    return redirect("login.html")


def login(request):
    if request.method != 'POST':
        return render(request, 'login.html', {'form': LoginForm()})

    form = LoginForm(request.POST)
    if not form.is_valid():
        return render(request, 'login.html', {'form': form})
    data = form.cleaned_data

    user = auth.authenticate(username=data['username'], password=data['password'])
    if user is None:
        messages.warning(request, 'Nieprawidłowa nazwa użytkownika lub hasło!')
        return render(request, 'login.html', {'form': form})
    if not user.is_active:
        messages.warning(request, 'To konto jest nieaktywne!')
        return render(request, 'login.html', {'form': form})
    auth.login(request, user)
    messages.success(request, 'Zalogowano pomyślnie!')
    return redirect(request.GET.get('next', '/'))


def logout(request):
    if request.user.is_authenticated():
        auth.logout(request)
        messages.success(request, "Wylogowano pomyślnie!")
    return redirect('/')


@user_passes_test(logged_in)
def test(request, task_id):
    if request.method != 'POST':
        return render(request, 'show_task.html', {'task_id': task_id})

    task = Task.objects.filter(pk=task_id)
    if len(task) == 0:
        messages.warning(request, 'Nieznane zadanie')
        return redirect('/')

    code = request.POST['code']
    sol = Solution (**{'code': code.encode ('utf-8'), 'user': request.user, 'task': task[0], 'date': timezone.now()})
    sol.save()
    que = Query (**{'solution': sol})
    que.save()
    
    taskevent.set ()
    if not testthread.isAlive():
        testthread.start ()

    return redirect('/')


@user_passes_test(logged_in)
def download_test(request, test_id):
    test = Test.objects.filter(pk=test_id)
    if len(test) == 0:
        messages.warning(request, 'Nieznany test!')
        return redirect('/')
    task = test.task
    file_path = os.path.join(TASKS_DIR, task.clear_name, 'tests', test[0].name + '.in')
    response = HttpResponse(FileWrapper(open(file_path, 'r')), content_type='application/force-download')
    response['Content-Length'] = os.path.getsize(file_path)
    return response


@user_passes_test(logged_in)
def show_solutions(request):
    if request.user.is_staff:
        solutions = Solution.objects.all ()
    else:
        solutions = Solution.objects.filter(user=request.user)
    return render(request, 'show_solutions.html', {'solutions': reversed(solutions)})


def show_solution(request, solution_id):
    solution = Solution.objects.filter (pk = solution_id)
    if len(solution) == 0:
        return redirect ("/show_solutions")
    if (not request.user.is_staff) and (solution[0].user != request.user):
        messages.warning(request, u'Brak uprawnień')
        return redirect ("/show_solutions")

    return render(request, 'show_solution.html', {
                                                  'solution': solution[0],
                                                  'codehtml': mark_safe(escape(solution[0].code).replace('\n', '<br>')),
                                                  'results': json.loads(solution[0].results)
                                                  })

@user_passes_test(logged_in)
def show_query(request):
    if request.user.is_staff:
        query = Query.objects.all ()
    else:
        query = Query.objects.filter(solution__user = request.user)
    return render(request, 'show_query.html', {'query': query})


@user_passes_test(is_admin)
def add_task(request):
    if request.method != 'POST':
        return render(request, 'add_task.html', {'form': AddTaskForm()})

    form = AddTaskForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'add_task.html', {'form': form})

    data = form.cleaned_data
    clear_name = data['clear_name'] = clear(data['name'])

    if Task.objects.filter(clear_name=clear_name):
        messages.warning(request, u'Zadanie o tej nazwie już istnieje!')
        return render(request, 'add_task.html', {'form': form})

    os.system('mkdir %s' % os.path.join(TASKS_DIR, clear_name))
    with open(os.path.join(TASKS_DIR, clear_name, 'info'), 'w') as f:
        f.write('Nazwa zadania: %s\n' % data['name'].encode('utf-8'))
        f.write('Limit pamięci: %d\n' % data['memlimit'])
        f.write('Autor: %s\n' % request.user)

    data['author'] = request.user
    data['description'] = data['description'].read()

    task = Task(**data)
    task.save()
    messages.success(request, u'Zadanie utworzone pomyślnie!')
    return redirect('/')


@user_passes_test(is_admin)
def manage_tasks(request):
    return render(request, 'manage_tasks.html', {'tasks': Task.objects.all()})


@user_passes_test(is_admin)
def manage_task(request, task_id):
    tasks = Task.objects.filter(pk=int(task_id))
    if len(tasks) == 0:
        messages.warning(request, 'Nieznane zadanie!')
        return redirect('/manage_tasks')

    task = tasks[0]
    if request.method != 'POST':
        initial = tasks[0].__dict__
        form = ChangeTaskForm(initial=initial)
        return render(request, 'manage_task.html', {'task': task, 'form': form})

    form = ChangeTaskForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'manage_task.html', {'task': task, 'form': form})

    data = form.cleaned_data
    clear_name = data['clear_name'] = clear(data['name'])

    if clear_name != task.clear_name:
        if Task.objects.filter(clear_name=clear_name):
            messages.warning(request, u'Zadanie o tej nazwie już istnieje!')
            return render(request, 'manage_task.html', {'task': task, 'form': form})
        os.system('mv %s %s' % (os.path.join(TASKS_DIR, task.clear_name), os.path.join(TASKS_DIR, clear_name)))

    fields = ('name', 'clear_name', 'memlimit', 'author')
    for field in fields:
        if field not in data or not data[field]:
            data[field] = getattr(task, field)

    with open(os.path.join(TASKS_DIR, clear_name, 'info'), 'w') as f:
        f.write('Nazwa zadania: %s\n' % data['name'].encode('utf-8'))
        f.write('Limit pamięci: %d\n' % data['memlimit'])
        f.write('Autor: %s\n' % data['author'])

    for field in fields:
        if field in data and data[field]:
            setattr(task, field, data[field])

    if 'description' in request.FILES:
        task.description = request.FILES['description'].read()

    task.save()
    messages.success(request, u'Zadanie zmodyfikowane pomyślnie!')
    return redirect('/')


@user_passes_test(is_admin)
def manage_tests(request, task_id):
    tasks = Task.objects.filter(pk=int(task_id))
    if len(tasks) == 0:
        messages.warning(request, 'Nieznane zadanie!')
        return redirect('/manage_tasks')
    task = tasks[0]
    tests = Test.objects.filter(task=task)

    change_test_formset = formset_factory(ChangeTestForm, extra=0, can_delete=True)

    if request.method != 'POST':
        formset = change_test_formset(initial=[test.__dict__ for test in tests])
        return render(request, 'manage_tests.html', {'task': task, 'formset': formset})

    formset = change_test_formset(request.POST, request.FILES)
    if not formset.is_valid():
        return render(request, 'manage_tests.html', {'task': task, 'formset': formset})

    for test, form in zip(tests, formset):
        data = form.cleaned_data
        tests_path = os.path.join(TASKS_DIR, task.clear_name, 'tests')
        if data['DELETE']:
            os.system('rm {0}.in {0}.out'.format(os.path.join(tests_path, test.name)))
            test.delete()
        else:
            test.points = data['points']
            test.timelimit = data['timelimit']

            name = clear(data['name'])
            if name != test.name:
                if len(Test.objects.filter(task=task, name=name)) > 0:
                    messages.warning(request, u'Zmiana nazwy testu z %s na %s zakończona niepowodzeniem'
                                              u'- nazwa zajęta' % (test.name, name))
                    continue
                os.system('mv %s.in %s.in' % (os.path.join(tests_path, test.name), os.path.join(tests_path, name)))
                os.system('mv %s.out %s.out' % (os.path.join(tests_path, test.name), os.path.join(tests_path, name)))
                test.name = name

            if data['input'] is not None:
                save_file(data['input'], os.path.join(tests_path, name + '.in'))
            if data['output'] is not None:
                save_file(data['output'], os.path.join(tests_path, name + '.out'))

            test.save()

    messages.success(request, 'Zmiany zastosowane')
    return redirect('/manage_task/%d/tests' % task.id)

@user_passes_test(is_admin)
def add_test(request, task_id):
    tasks = Task.objects.filter(pk=int(task_id))
    if len(tasks) == 0:
        messages.warning(request, 'Nieznane zadanie!')
        return redirect('/manage_tasks')
    task = tasks[0]

    if request.method != 'POST':
        return render(request, 'add_test.html', {'task': task, 'form': AddTestForm()})

    form = AddTestForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, 'add_test.html', {'task': task, 'form': form})

    data = form.cleaned_data
    tests_path = os.path.join(TASKS_DIR, task.clear_name, 'tests')
    if not os.path.exists(tests_path):
        os.system('mkdir %s' % tests_path)  # zakładam że nie istnieje tylko folder "tests"

    name = clear(data['name'])
    if len(Test.objects.filter(name=name)) > 0:
        messages.warning(request, u'Test o podanej nazwie już istnieje!')
        return render(request, 'add_test.html', {'task': task, 'form': form})

    try:
        save_file(request.FILES['input'], os.path.join(tests_path, '%s.in' % name))
        save_file(request.FILES['output'], os.path.join(tests_path, '%s.out' % name))
    except:
        messages.warning(request, u'Błąd w trakcie zapisywania testu!')
        return render(request, 'add_test.html', {'task': task, 'form': form})

    Test(task=task, name=name, timelimit=data['timelimit'], points=data['points']).save()

    messages.success(request, 'Utworzono test!')
    return redirect('/manage_task/%d/tests' % task.id)


@user_passes_test(is_admin)
def remove_task(request, task_id):
    t = Task.objects.filter(pk=task_id)
    if len(t) == 0:
        messages.warning(request, u'Nieznane zadanie!')
    else:
        path = os.path.join(TASKS_DIR, t[0].clear_name)
        if os.path.exists(path):
            os.system('rm -rf %s' % path)
        messages.success(request, u'Zadanie "%s" usunięte!' % t[0].name)
        t[0].delete()
    return redirect('/manage_tasks')
