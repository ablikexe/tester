# coding: utf-8
from django import forms


class AddTaskForm(forms.Form):
    name = forms.CharField(label=u'Nazwa zadania', max_length=100)
    memlimit = forms.IntegerField(label=u'Limit pamięci', min_value=1, max_value=1024)
    description = forms.fields.FileField(label=u'Treść zadania')
    author_solution = forms.FileField(label=u'Rozwiązanie wzorcowe', required=False)
    generator = forms.FileField(label=u'Program generujący testy (opcjonalne)', required=False)
    checker = forms.FileField(label=u'Program sprawdzający poprawność wyniku (opcjonalne)', required=False)


class LoginForm(forms.Form):
    username = forms.CharField(label=u'Nazwa użytkownika', max_length=30)
    password = forms.CharField(label=u'Hasło', widget=forms.PasswordInput)
