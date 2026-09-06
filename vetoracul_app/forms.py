from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from .models import User, EmailVerificationCode

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(max_length=20, required=False, label='Телефон')
    city = forms.CharField(max_length=100, required=False, label='Город')
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, initial='user', label='Роль')

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'city', 'role', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Имя пользователя или Email', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label='Новый пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class VerificationCodeForm(forms.Form):
    code = forms.CharField(
        label='Код подтверждения',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите 6-значный код'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data['code']
        try:
            verif = EmailVerificationCode.objects.get(user=self.user)
        except EmailVerificationCode.DoesNotExist:
            raise forms.ValidationError('Код не найден. Запросите повторную отправку.')
        if not verif.is_valid():
            raise forms.ValidationError('Код истёк. Запросите новый код.')
        if verif.code != code:
            raise forms.ValidationError('Неверный код.')
        return code