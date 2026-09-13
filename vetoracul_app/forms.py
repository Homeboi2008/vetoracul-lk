from django import forms
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm

from .models import Diagnosis, Reminder, User, EmailVerificationCode, Folder, Document



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
    
class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ('name', 'parent')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название папки'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner', None)
        super().__init__(*args, **kwargs)
        if self.owner:
            # Показываем только папки этого владельца
            self.fields['parent'].queryset = Folder.objects.filter(owner=self.owner)
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = '— Корень —'

    def clean_name(self):
        name = self.cleaned_data['name']
        parent = self.cleaned_data.get('parent')
        if Folder.objects.filter(owner=self.owner, parent=parent, name=name).exists():
            raise forms.ValidationError('Папка с таким именем уже существует здесь.')
        return name


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('title', 'file', 'date', 'folder', 'description')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'folder': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['folder'].required = False
        self.fields['folder'].empty_label = '— Без папки —'
        if self.user:
            self.fields['folder'].queryset = Folder.objects.filter(owner=self.user)

from django import forms
from .models import Pet

class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ('name', 'animal_type', 'gender', 'birth_date', 'weight', 'co_owners')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Барсик'}),
            'animal_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Кошка'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'co_owners': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # В совладельцы можно добавлять только обычных пользователей, кроме самого владельца
        if self.user:
            self.fields['co_owners'].queryset = User.objects.filter(
                role='user'
            ).exclude(pk=self.user.pk)
        self.fields['co_owners'].required = False
        self.fields['birth_date'].required = False

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None and weight <= 0:
            raise forms.ValidationError('Вес должен быть больше нуля.')
        return weight

class DiagnosisForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        fields = ('diagnosis_text', 'date', 'status', 'vet')
        widgets = {
            'diagnosis_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Опишите диагноз'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'vet': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Врачей может выбирать только ветеринар; обычный пользователь поле не видит
        if self.user and self.user.role != 'vet':
            self.fields.pop('vet', None)
        else:
            self.fields['vet'].queryset = User.objects.filter(role='vet')
            self.fields['vet'].required = False

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise forms.ValidationError('Дата диагноза не может быть в будущем.')
        return date


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('title', 'file', 'date', 'folder', 'description')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'folder': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['folder'].required = False
        self.fields['folder'].empty_label = '— Без папки —'
        if self.user:
            self.fields['folder'].queryset = Folder.objects.filter(owner=self.user)


class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ('title', 'description', 'reminder_type', 'date', 'time', 'status')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Запись к врачу'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reminder_type': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['time'].required = False
        self.fields['description'].required = False