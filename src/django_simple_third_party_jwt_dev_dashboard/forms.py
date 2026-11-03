"""Two user forms kept for projects that import them; see compat.py (they can go in 1.0)."""
from django import forms
from django.contrib.auth.models import User


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username",)


class UserForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    username = forms.CharField(label="Username")

    class Meta:
        model = User
        fields = ["username", "password"]
