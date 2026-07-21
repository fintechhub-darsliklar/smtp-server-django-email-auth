from django import forms
from crispy_forms.helper import FormHelper


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email yozing.",
        widget=forms.EmailInput(attrs={'class': 'w-25'}),
        help_text="Email yozishingiz kerak!"
    )
    password = forms.CharField(
        label="Parol yozing.",
        widget=forms.PasswordInput(attrs={'class': 'w-25'}),
        max_length=100,
        help_text="Parol yozishingiz kerak!"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'


class RegisterForm(forms.Form):
    first_name = forms.CharField(
        label="Ism yozing.",
        widget=forms.TextInput(attrs={'class': 'w-25'}),
        help_text="Ism yozishingiz kerak!"
    )
    email = forms.EmailField(
        label="Email yozing.",
        widget=forms.EmailInput(attrs={'class': 'w-25'}),
        help_text="Email yozishingiz kerak!"
    )
    password = forms.CharField(
        label="Parol yozing.",
        widget=forms.PasswordInput(attrs={'class': 'w-25'}),
        max_length=100,
        help_text="Parol yozishingiz kerak!"
    )
    password_confirm = forms.CharField(
        label="Parol qaytadan yozing.",
        widget=forms.PasswordInput(attrs={'class': 'w-25'}),
        max_length=100,
        help_text="Parol yozishingiz kerak!"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'

