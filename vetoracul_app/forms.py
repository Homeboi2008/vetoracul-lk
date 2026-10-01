from django import forms
from django.utils import timezone
from django.contrib.auth.forms import (
    UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
)
from .models import Diagnosis, Reminder, User, EmailVerificationCode, Folder, Document, Pet, PetCoOwner


# =========================================================
# Утилита для классов виджетов
# =========================================================
def apply_input_classes(fields, select_fields=()):
    for name, field in fields.items():
        css = 'form-input form-select' if name in select_fields else 'form-input'
        field.widget.attrs.update({'class': css})


# =========================================================
# Пользовательские формы аутентификации
# =========================================================
class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации обычного пользователя. Роль всегда 'user'."""
    first_name = forms.CharField(max_length=50, required=True, label='Имя')
    last_name = forms.CharField(max_length=50, required=True, label='Фамилия')
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(max_length=20, required=True, label='Телефон')

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем поле username — генерируем из email автоматически
        self.fields.pop('username', None)
        apply_input_classes(self.fields)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Введите имя'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Введите фамилию'
        self.fields['email'].widget.attrs['placeholder'] = 'example@mail.ru'
        self.fields['phone'].widget.attrs['placeholder'] = '+7 (___) ___-__-__'
        self.fields['password1'].widget.attrs['placeholder'] = 'Минимум 8 символов'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторите пароль'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Генерируем уникальный username из email
        base = self.cleaned_data['email'].split('@')[0]
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{counter}'
            counter += 1
        user.username = username
        user.role = 'user'  # Жёстко фиксируем роль
        if commit:
            user.save()
        return user


class VetRegistrationForm(UserCreationForm):
    """Расширенная форма регистрации ветеринара."""
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(max_length=20, required=True, label='Телефон')
    first_name = forms.CharField(max_length=50, required=True, label='Имя')
    last_name = forms.CharField(max_length=50, required=True, label='Фамилия')
    city = forms.CharField(max_length=100, required=False, label='Город')
    specialization = forms.CharField(max_length=100, required=True, label='Специализация')
    education = forms.CharField(max_length=200, required=True, label='Образование (вуз)')
    grad_year = forms.IntegerField(required=True, label='Год окончания', min_value=1950, max_value=2030)
    license_number = forms.CharField(max_length=50, required=True, label='Номер лицензии')
    experience = forms.IntegerField(required=True, label='Стаж (лет)', min_value=0, max_value=60)
    clinic = forms.CharField(max_length=200, required=True, label='Место работы')

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_input_classes(self.fields)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'vet'
        user.is_active = False
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.city = self.cleaned_data.get('city', '')
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-input'}))


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label='Новый пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    new_password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput(attrs={'class': 'form-input'}))


class VerificationCodeForm(forms.Form):
    code = forms.CharField(
        label='Код подтверждения',
        max_length=6, min_length=6,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Введите 6-значный код'})
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


# =========================================================
# Питомец
# =========================================================
class PetForm(forms.ModelForm):
    co_owners = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-input', 'id': 'id_co_owners'}),
        label='Совладельцы',
    )

    class Meta:
        model = Pet
        fields = (
            'name', 'animal_type', 'breed', 'gender', 'birth_date',
            'weight', 'health_status', 'photo', 'notes',
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name in ('photo', 'co_owners'):
                continue
            if name in {'gender', 'health_status'}:
                field.widget.attrs.update({'class': 'form-input form-select'})
            else:
                field.widget.attrs.update({'class': 'form-input'})

        if self.user:
            self.fields['co_owners'].queryset = (
                User.objects.filter(role='user').exclude(pk=self.user.pk)
            )

        self.fields['birth_date'].required = False
        self.fields['breed'].required = False
        self.fields['photo'].required = False
        self.fields['notes'].required = False
        self.fields['co_owners'].required = False

        # Начальные значения для Select2
        if self.instance.pk:
            self.fields['co_owners'].initial = list(
                self.instance.co_owners.values_list('pk', flat=True)
            )

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight is not None and weight <= 0:
            raise forms.ValidationError('Вес должен быть больше нуля.')
        return weight

    def get_co_owner_levels_json(self):
        """JSON со текущими уровнями доступа для JS в шаблоне."""
        import json
        levels = {}
        if self.instance.pk:
            for link in self.instance.co_owner_links.all():
                levels[str(link.user_id)] = link.access_level
        return json.dumps(levels)

    def save(self, commit=True):
        pet = super().save(commit=commit)
        if not commit:
            return pet

        selected = self.cleaned_data.get('co_owners') or []
        selected_ids = {u.pk for u in selected}

        # Удаляем тех, кто больше не выбран
        for link in pet.co_owner_links.all():
            if link.user_id not in selected_ids:
                link.delete()

        # Обновляем/создаём
        for user in selected:
            level = (self.data.get(f'co_owner_level_{user.pk}') or 'read').strip()
            if level not in dict(PetCoOwner.AccessLevel.choices):
                level = PetCoOwner.AccessLevel.READ

            link = pet.co_owner_links.filter(user=user).first()
            if link:
                if link.access_level != level:
                    link.access_level = level
                    link.save(update_fields=['access_level'])
            else:
                PetCoOwner.objects.create(pet=pet, user=user, access_level=level)

        return pet


# =========================================================
# Диагноз
# =========================================================
class DiagnosisForm(forms.ModelForm):
    new_health_status = forms.ChoiceField(
        choices=Pet.HealthStatus.choices,
        required=False,
        label='Обновить состояние питомца',
        widget=forms.Select(attrs={'class': 'form-input form-select'}),
        help_text='Оставьте пустым, чтобы не менять текущее состояние',
    )

    class Meta:
        model = Diagnosis
        fields = ('diagnosis_text', 'treatment', 'date', 'status', 'vet')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Установим текущее состояние питомца как начальное значение
        if self.instance and self.instance.pk and self.instance.pet_id:
            self.fields['new_health_status'].initial = self.instance.pet.health_status
        elif 'initial' in kwargs and kwargs['initial']:
            pass

        apply_input_classes(self.fields, select_fields={'status', 'vet'})

        if self.user and self.user.role != 'vet':
            self.fields.pop('vet', None)
        else:
            self.fields['vet'].queryset = User.objects.filter(role='vet')
            self.fields['vet'].required = False
        self.fields['treatment'].required = False

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise forms.ValidationError('Дата диагноза не может быть в будущем.')
        return date


# =========================================================
# Документ
# =========================================================
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('title', 'file', 'date', 'folder', 'description')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        apply_input_classes(self.fields, select_fields={'folder'})
        self.fields['folder'].required = False
        self.fields['folder'].empty_label = '— Без папки —'
        if self.user:
            self.fields['folder'].queryset = Folder.objects.filter(owner=self.user)


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('title', 'file', 'date', 'folder', 'description')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        apply_input_classes(self.fields, select_fields={'folder'})
        self.fields['folder'].required = False
        self.fields['folder'].empty_label = '— Без папки —'
        if self.user:
            self.fields['folder'].queryset = Folder.objects.filter(owner=self.user)


# =========================================================
# Напоминание
# =========================================================
class ReminderForm(forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ('title', 'description', 'reminder_type', 'date', 'time', 'status')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_input_classes(self.fields, select_fields={'reminder_type', 'status'})
        self.fields['time'].required = False
        self.fields['description'].required = False


# =========================================================
# Папка
# =========================================================
class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ('name', 'parent')

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner', None)
        super().__init__(*args, **kwargs)
        apply_input_classes(self.fields, select_fields={'parent'})
        if self.owner:
            self.fields['parent'].queryset = Folder.objects.filter(owner=self.owner)
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = '— Корень —'

    def clean_name(self):
        name = self.cleaned_data['name']
        parent = self.cleaned_data.get('parent')
        if Folder.objects.filter(owner=self.owner, parent=parent, name=name).exists():
            raise forms.ValidationError('Папка с таким именем уже существует здесь.')
        return name
    
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'city', 'photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'photo':
                continue
            field.widget.attrs.update({'class': 'form-input'})
        self.fields['photo'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Этот email уже занят.')
        return email


class NotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('notify_appointments', 'notify_vaccinations', 'notify_urgent', 'notify_news')