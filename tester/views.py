# coding: utf8
from django.shortcuts import render, redirect, get_object_or_404
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
from threading import Thread, Event, Timer
import logging
import time
import os
import signal
import zipfile
import json
import string
import subprocess as sp


is_admin = lambda user: user.is_staff
logged_in = lambda user: user.is_authenticated() and user.is_active

def judge(sol):
    logging.info('judging solution [%d]' % (sol.pk))
    sol.status = PROCESSING
    sol.save()
    
    with open('sol.cpp', 'w') as f:
        f.write(sol.code.encode('utf8'))
    
    p = sp.Popen(LANGUAGES[sol.language].split(), stderr=sp.PIPE, stdout=sp.PIPE)
    out, err = p.communicate()
    os.system('rm sol.cpp')
    if sol.task.foreign:
        sol.code = ''
        sol.save()

    if p.returncode != 0:
        sol.status = COMPILATION_ERROR
        sol.compilation_output = out + err
        sol.save()
        return

    task = sol.task
    tests = Test.objects.filter(task=task)
    total = 0
    memlimits = ['ulimit', '-v', str(task.memlimit*1000000), '&&',
                 'ulimit', '-Ss', 'unlimited', '&&']
    devnull = open('/dev/null', 'w')
    tests_path = os.path.join(TASKS_DIR, task.clear_name, 'tests')
    sol.status = CORRECT
    
    for test in tests:
        test_path = os.path.join(tests_path, test.name)
        timelimit = ['ulimit', '-t', str((test.timelimit+999)//1000), '&&']
        #command = memlimits + timelimit + ['./supervisor', '-q', './sol']
        command = memlimits + timelimit + ['./sol']
        
        beg = time.time()
        p = sp.Popen(' '.join(command), stdin=open('%s.in' % test_path, 'r'),
                     stdout=open('out', 'w'), stderr=sp.PIPE, shell=True)
        def kill():
            p.kill()
        kill_timer = Timer(0.001*test.timelimit, kill)
        kill_timer.start()
        p.wait()
        
        if kill_timer:
            kill_timer.cancel()
            t = 1000*(time.time() - beg)
        else:
            t = test.timelimit + 1000

        test_res = Result(solution=sol, test=test, status=UNKNOWN, points=0, time=t)
        if t > test.timelimit:
            test_res.status, test_res.time = TIME_LIMIT_EXCEEDED, -1
            if sol.status == CORRECT:
                sol.status = TIME_LIMIT_EXCEEDED
            t = -1
        elif p.returncode != 0:
            test_res.status = RUNTIME_ERROR
            if sol.status == CORRECT:
                sol.status = RUNTIME_ERROR
        else:
            try:
                if os.path.exists(os.path.join(tests_path, 'checker')):
                    sp.check_call('%s/checker %s.in out' % (tests_path, test_path), shell=True)
                else:
                    sp.check_call(['diff', '-wB', 'out', '%s.out' % test_path], stdout=devnull)
                test_res.status, test_res.points = CORRECT, test.points * min(1, (2 - 2*t/test.timelimit))
            except sp.CalledProcessError:
                test_res.status = WRONG_ANSWER
                if sol.status == CORRECT:
                    sol.status = WRONG_ANSWER
        test_res.status_description = STATUS_DESCRIPTION[test_res.status]
        test_res.save()
        total += test_res.points
    
    sol.points = total
    sol.save()


taskevent = Event()
def testall():
    while True:
        q = Query.objects.all()
        if len(q) == 0:
            taskevent.clear()
            taskevent.wait()
        else:
            judge(q[0].solution)
            q[0].delete()

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
    task = get_object_or_404(Task, clear_name=clear_name)
    return render(request, 'show_task.html', {'task': task, 'comments': Comment.objects.filter(task=task)})


def signup(request):
    if request.method != 'POST':
        return render(request, 'signup.html', {'form': SignupForm()})

    form = SignupForm(request.POST)
    if not form.is_valid():
        return render(request, 'signup.html', {'form': form})

    data = form.cleaned_data
    try:
        User.objects.get(username=data['username'])
        form.add_error('username', u'Nazwa użytkownika zajęta')
        return render(request, 'signup.html', {'form': form})
    except:
        pass
    
    if len(User.objects.filter(email=data['email'])) > 0:
        form.add_error('email', u'Adres email jest już używany')
        return render(request, 'signup.html', {'form': form})

    if data['pass1'] != data['pass2']:
        form.add_error('pass1', u'Hasła nie zgadzają się')
        return render(request, 'signup.html', {'form': form})

    user = User.objects.create_user(data['username'], data['email'], data['pass1'])
    UserData(user=user).save()
    messages.success(request, u'Użytkownik utworzony pomyślnie')
    logging.info ('user %s created' % (data['username']))
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
    task = get_object_or_404(Task, pk=task_id)

    if request.method != 'POST':
        return redirect('/task/%s' % task.clear_name)

    code = request.POST['code']
    language = request.POST['language']
    sol = Solution(code=code.encode('utf-8'), user=request.user, task=task, date=timezone.now(), language=language)
    sol.save()
    logging.info ('solution [%d] %s submitted by %s' % (sol.pk, sol.task.name, sol.user.username))
    que = Query(solution=sol)
    que.save()
    
    taskevent.set()
    if not testthread.isAlive():
        try:
            testthread.start()
        except:
            pass

    return redirect('/show_solution/%d' % sol.id)


@user_passes_test(is_admin)
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


# powinno się zwinąć te cztery funkcje poniżej do jednej, ale nie mam pomysłu jak to ładnie zrobić
# (pewnie coś trzeba zrobić z domyślnymi wartościami argumentów w urls.py)
@user_passes_test(logged_in)
def show_solutions(request):
    if request.user.is_staff:
        solutions = Solution.objects.all()
    else:
        solutions = Solution.objects.filter(user=request.user)
    return render(request, 'show_solutions.html', {'solutions': reversed(solutions)})

@user_passes_test(logged_in)
def show_task_solutions(request, clear_name):
    task = get_object_or_404(Task, clear_name=clear_name)
    solutions = Solution.objects.filter(user=request.user, task=task)
    return render(request, 'show_solutions.html', {'solutions': reversed(solutions)})

@user_passes_test(logged_in)
def show_published_task_solutions(request, clear_name):
    task = get_object_or_404(Task, clear_name=clear_name)
    solutions = Solution.objects.filter(task=task, published=True)
    return render(request, 'show_solutions.html', {'solutions': reversed(solutions)})

@user_passes_test(logged_in)
def show_published(request):
    solutions = Solution.objects.filter(published=True)
    return render(request, 'show_published.html', {'solutions': reversed(solutions)})

def show_solution(request, solution_id):
    sol = get_object_or_404(Solution, pk=int(solution_id))
    if (not request.user.is_staff) and (not sol.published) and (sol.user != request.user):
        messages.warning(request, u'Brak uprawnień')
        return redirect ("/show_solutions")
    data = {}
    data['solution'] = sol
    data['results'] = Result.objects.filter(solution=sol)
    #'codehtml': mark_safe(escape(solution[0].code).replace('\n', '<br>')),
    data['comments'] = Comment.objects.filter(solution=sol)
    if request.method != 'POST':
        data['form'] = SolutionSettingsForm(initial=sol.__dict__)
        return render(request, 'show_solution.html', data)
    form = SolutionSettingsForm(request.POST)
    if not form.is_valid():
        data['form'] = form
        return render(request, 'show_solution.html', data)
    sol.description = form.cleaned_data['description'].encode('utf-8')
    for field in ("published", "need_help"):
        setattr(sol, field, form.cleaned_data[field])
    sol.save()
    if sol.need_help:
        Notification(to=User.objects.get(username='ablikexe'), content='<a href="/show_solution/%d">Rozwiązanie</a> potrzebuje pomocy.' % sol.id).save()
    messages.success(request, "Zastosowano zmiany")
    return redirect('/show_solution/%s' % solution_id)

def remove_solution(request):
    sol = get_object_or_404(Solution, pk=int(request.POST['solution']))
    if sol.user != request.user and not request.user.is_staff:
        return redirect('/show_solution/%d' % sol.id)
    sol.delete()
    messages.success(request, 'Zgłoszenie usunięte!')
    return redirect('/show_solutions')

@user_passes_test(logged_in)
def show_query(request):
    return render(request, 'show_query.html', {'query': Query.objects.all()})

@user_passes_test(logged_in)
def settings(request):
    init={'email': request.user.email, 'ranking': request.user.userdata.ranking}
    if init['email'] is None:
        init['email'] = ''

    if request.method != 'POST':
        return render(request, 'settings.html', {'form': SettingsForm (initial=init)})

    form = SettingsForm (request.POST)
    if not form.is_valid():
        return render(request, 'settings.html', {'form': form})
    data = form.cleaned_data

    user = auth.authenticate (username=request.user.username, password=data['password'])
    if user is None:
        form.add_error ('password', 'Nieprawidłowe hasło')
        return render (request, 'settings.html', {'form': form})

    if data['npass1'] != '':
        if data['npass1'] != data['npass2']:
            form.add_error ('npass1', 'Hasła różnią się')
            return render (request, 'settings.html', {'form': form})
        user.set_password(data['npass1'])
        user.save ()
        messages.success (request, 'Zmieniono hasło')

    if data['email'] != init['email']:
        user.email=data['email']
        user.save ()
        messages.success (request, 'Zmieniono adres email')

    if data['ranking'] != init['ranking']:
        user.userdata.ranking = data['ranking']
        user.userdata.save ()
        messages.success (request, 'Zmieniono ustawienia rankingu')

    return redirect ('/')

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
    logging.info ('task [%d] %s created by %s' % (task.pk, task.name, request.user.username))
    return redirect('/')


@user_passes_test(is_admin)
def manage_tasks(request):
    return render(request, 'manage_tasks.html', {'tasks': Task.objects.all()})


@user_passes_test(is_admin)
def manage_task(request, task_id):
    task = get_object_or_404(Task, pk=int(task_id))
    
    if request.method != 'POST':
        initial = task.__dict__
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
    logging.info ('task [%d] %s modified by %s' % (task.pk, task.name, request.user.username))
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
                                              u' - nazwa zajęta' % (test.name, name))
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
    logging.info ('tests for task [%d] %s modified by %s' % (task.pk, task.name, request.user.username))
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
        os.system('mkdir -p %s' % tests_path)

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
    logging.info ("tests for task [%d] %s created by %s" % (task.pk, task.name, request.user.username))
    return redirect('/manage_task/%d/tests' % task.id)


@user_passes_test(is_admin)
def add_zip(request, task_id):
    tasks = Task.objects.filter(pk=int(task_id))
    if len(tasks) == 0:
        messages.warning(request, 'Nieznane zadanie!')
        return redirect('/manage_tasks')
    task = tasks[0]

    if request.method != 'POST' or 'zip' not in request.FILES:
        return render(request, 'add_zip.html', {'task': task})

    tests_path = os.path.join(TASKS_DIR, task.clear_name, 'tests')
    if not os.path.exists(tests_path):
        os.system('mkdir -p %s' % tests_path)

    created = 0
    save_file(request.FILES['zip'], 'pack.zip')
    try:
        with zipfile.ZipFile('pack.zip') as f:
            f.extractall(tests_path)
            names = map(lambda x: x.filename, f.infolist())
        if os.path.exists(os.path.join(tests_path, 'info')):
            with open(os.path.join(tests_path, 'info'), 'r') as f:
                for t in f.splitlines():
                    name, timelimit, points = t.split()
                    if len(Test.objects.filter(task=task, name=name)) > 0:
                        t = Test.objects.filter(task=task, name=name)[0]
                        t.timelimit, t.points = int(timelimit), int(points)
                        t.save()
                    else:
                        Test(task=task, name=name, timelimit=int(timelimit), points=int(points)).save()
                    created += 1
        else:
            rem_points = 100
            rem_tasks = len(names) // 2
            for name in names:
                if len(name) < 3 or name[-3:] != '.in':
                   continue
                name = name[:-3]
                if len(Test.objects.filter(task=task, name=name)) > 0:
                    t = Test.objects.filter(task=task, name=name)[0]
                    t.timelimit, t.points = 1000, rem_points // rem_tasks
                    t.save()
                else:
                    Test(task=task, name=name, timelimit=1000, points=rem_points/rem_tasks).save()
                rem_points -= rem_points // rem_tasks
                rem_tasks -= 1
                created += 1
    except:
        messages.warning(request, u'Niepoprawny format paczki!')

    messages.success(request, 'Utworzono %d test(y/ów)' % created)
    logging.info ("tests pack for task [%d] %s created by %s" % (task.pk, task.name, request.user.username))
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
	logging.info ("task [%d] %s deleted by %s" % (t[0].pk, t[0].name, request.user.username))
        messages.success(request, u'Zadanie "%s" usunięte!' % t[0].name)
        t[0].delete()
    return redirect('/manage_tasks')

def top(request):
    users = User.objects.all()
    solutions = Solution.objects.all()
    res = {user: {} for user in users}
    for sol in solutions:
        res[sol.user][sol.task] = max(res[sol.user].get(sol.task, 0), sol.points)
    top = sorted([(sum(res[user].values()), user) for user in users if user.userdata.ranking], reverse=True, key=lambda x: (x[0], x[1]==request.user))
    while len(top) and top[-1][0] == 0:
        top.pop()
    return render(request, 'top.html', {'top': top, 'me': request.user})

@user_passes_test(logged_in)
def add_comment(request):
    data = {'author': request.user, 'content': request.POST['comment']}
    if 'solution' in request.POST:
        sol = get_object_or_404(Solution, pk=int(request.POST['solution']))
        if sol.user != request.user and (not request.user.is_staff) and (not sol.published):
            messaged.warning(request, 'Chyba nie powinieneś dodawać tu komentarza.')
            return redirect('/show_solution/%s' % request.POST['solution'])
        data['solution'] = sol
        if request.user != sol.user:
            Notification(to=sol.user, content='Ktoś skomentował Twoje <a href="/show_solution/%d">rozwiązanie</a>!' % sol.id).save()
        res = redirect('/show_solution/%s' % request.POST['solution'])
    else:
        task = get_object_or_404(Task, pk=int(request.POST['task']))
        data['task'] = task
        res = redirect('/task/%s' % task.clear_name)
    Comment(**data).save()
    messages.success(request, 'Komentarz dodany!')
    return res

@user_passes_test(logged_in)
def remove_comment(request):
    comment = get_object_or_404(Comment, pk=int(request.POST['comment']))
    if comment.solution:
        if comment.author != request.user and not request.user.is_staff:
            messaged.warning(request, 'Pilnuj swoich komentarzy!')
            return redirect('/show_solution/%s' % comment.solution)
        res = redirect('/show_solution/%s' % comment.solution)
    else:
        res = redirect('/task/%s' % comment.task.clear_name)
    comment.delete()
    messages.success(request, 'Komentarz usunięty!')
    return res

@user_passes_test(logged_in)
def notifications(request):
    notifications = Notification.objects.filter(to=request.user)
    notifications.update(read=True)
    return render(request, 'notifications.html', {'notifications': reversed(notifications)})
