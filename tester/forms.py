# coding: utf-8
from django import forms


class AddTaskForm(forms.Form):
    name = forms.CharField(label=u'Nazwa zadania', max_length=100)
    memlimit = forms.IntegerField(label=u'Limit pamięci', min_value=1, max_value=1024)
    description = forms.fields.FileField(label=u'Treść zadania')


class ChangeTaskForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput)
    name = forms.CharField(label=u'Nazwa zadania', max_length=100)
    memlimit = forms.IntegerField(label=u'Limit pamięci', min_value=1, max_value=1024)
    description = forms.fields.FileField(label=u'Treść zadania', required=False)
    author_solution = forms.FileField(label=u'Rozwiązanie wzorcowe', required=False)
    generator = forms.FileField(label=u'Program generujący testy', required=False)
    checker = forms.FileField(label=u'Program sprawdzający poprawność wyniku', required=False)


class AddTestForm(forms.Form):
    input = forms.FileField(label=u'Dane wejściowe')
    output = forms.FileField(label=u'Poprawna odpowiedź')
    points = forms.IntegerField(label=u'Liczba punktów', min_value=0)
    timelimit = forms.IntegerField(label=u'Limit czasu (w milisekundach)', min_value=1)


class LoginForm(forms.Form):
    username = forms.CharField(label=u'Nazwa użytkownika', max_length=30)
    password = forms.CharField(label=u'Hasło', widget=forms.PasswordInput)


class SignupForm(forms.Form):
    username = forms.CharField(label=u'Nazwa użytkownika', max_length=30)
    email = forms.CharField(label=u'Adres e-mail', widget=forms.EmailInput)
    pass1 = forms.CharField(label=u'Hasło', widget=forms.PasswordInput)
    pass2 = forms.CharField(label=u'Powtórz hasło', widget=forms.PasswordInput)
