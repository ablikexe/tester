# coding: utf-8
from django import forms
from tester.limits import *


class AddTaskForm(forms.Form):
    name = forms.CharField(label=u'Nazwa zadania', max_length=100)
    memlimit = forms.IntegerField(label=u'Limit pamięci', min_value=1, max_value=1024)
    description = forms.fields.FileField(label=u'Treść zadania')

    def clean_description(self):
        f = self.cleaned_data.get('description')
        if not f:
            raise forms.ValidationError(u'To pole jest wymagane')
        if f._size > MAX_DESCRIPTION_SIZE:
            raise forms.ValidationError(u'Plik za duży')
        return f


class ChangeTaskForm(AddTaskForm):
    id = forms.IntegerField(widget=forms.HiddenInput)
    description = forms.fields.FileField(label=u'Treść zadania', required=False)

    def clean_description(self):
        f = self.cleaned_data['description']
        if f and f._size > MAX_DESCRIPTION_SIZE:
            raise forms.ValidationError(u'Plik za duży')
        return f


class AddTestForm(forms.Form):
    name = forms.CharField(label=u'Oznaczenie testu', min_length=1, max_length=20)
    input = forms.FileField(label=u'Dane wejściowe')
    output = forms.FileField(label=u'Poprawna odpowiedź')
    points = forms.IntegerField(label=u'Liczba punktów', min_value=0)
    timelimit = forms.IntegerField(label=u'Limit czasu (w milisekundach)', min_value=1, max_value=MAX_TIMELIMIT)

    def clean_input(self):
        f = self.cleaned_data['input']
        if f is not None and f._size > MAX_INPUT_SIZE:
            raise forms.ValidationError(u'Plik za duży')
        return f

    def clean_output(self):
        f = self.cleaned_data['output']
        if f is not None and f._size > MAX_OUTPUT_SIZE:
            raise forms.ValidationError(u'Plik za duży')
        return f

class ChangeTestForm(AddTestForm):
    input = forms.FileField(label=u'Dane wejściowe', required=False)
    output = forms.FileField(label=u'Poprawna odpowiedź', required=False)


class LoginForm(forms.Form):
    username = forms.CharField(label=u'Nazwa użytkownika', max_length=30)
    password = forms.CharField(label=u'Hasło', widget=forms.PasswordInput)


class SignupForm(forms.Form):
    username = forms.CharField(label=u'Nazwa użytkownika', max_length=30)
    email = forms.CharField(label=u'Adres e-mail', widget=forms.EmailInput)
    pass1 = forms.CharField(label=u'Hasło', widget=forms.PasswordInput)
    pass2 = forms.CharField(label=u'Powtórz hasło', widget=forms.PasswordInput)
