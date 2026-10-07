from django import forms
from django.utils import timezone
from django.contrib.auth.forms import (
    UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
)
from .models import Diagnosis, Reminder, User, EmailVerificationCode, Folder, Document, Pet, PetCoOwner, VetProfile, VetInviteToken


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
    first_name = forms.CharField(max_length=50, required=True, label='Имя')
    last_name = forms.CharField(max_length=50, required=True, label='Фамилия')
    middle_name = forms.CharField(max_length=50, required=False, label='Отчество')
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(max_length=20, required=True, label='Телефон')

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'middle_name', 'phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем поле username — генерируем из email автоматически
        self.fields.pop('username', None)
        apply_input_classes(self.fields)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Введите имя'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Введите фамилию'
        self.fields['middle_name'].widget.attrs['placeholder'] = 'Введите отчество (если есть)'
        self.fields['email'].widget.attrs['placeholder'] = 'example@mail.ru'
        self.fields['phone'].widget.attrs['placeholder'] = '+7 (___) ___-__-__'
        self.fields['password1'].widget.attrs['placeholder'] = 'Минимум 8 символов'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторите пароль'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        existing = User.objects.filter(email__iexact=email).first()
        if existing and existing.is_active:
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def save(self, commit=True):
        email = self.cleaned_data['email']
        existing = User.objects.filter(email__iexact=email, is_active=False).first()

        if existing:
            user = existing
            user.username = user.username  # оставляем как есть
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.middle_name = self.cleaned_data.get('middle_name', '')
            user.phone = self.cleaned_data['phone']
            user.role = 'user'
            user.set_password(self.cleaned_data['password1'])
            if commit:
                user.save()
            return user

        # Обычный путь
        user = super().save(commit=False)
        base = email.split('@')[0]
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f'{base}{counter}'
            counter += 1
        user.username = username
        user.role = 'user'
        if commit:
            user.save()
        return user


class VetRegistrationForm(UserCreationForm):
    """Форма регистрации ветеринара (по одноразовой ссылке)."""
    first_name = forms.CharField(max_length=50, required=True, label='Имя')
    last_name = forms.CharField(max_length=50, required=True, label='Фамилия')
    middle_name = forms.CharField(max_length=50, required=False, label='Отчество')
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(max_length=20, required=True, label='Телефон')
    city = forms.CharField(max_length=100, required=False, label='Город')

    specialization = forms.ChoiceField(
        choices=VetProfile.Specialization.choices,
        label='Специализация', required=True,
    )
    education = forms.CharField(
        max_length=200, required=True,
        label='Образование (вуз)',
        widget=forms.TextInput(attrs={'placeholder': 'МГАВМиБ им. Скрябина'}),
    )
    grad_year = forms.IntegerField(
        required=True, label='Год окончания',
        min_value=1950, max_value=2030,
    )
    license_number = forms.CharField(
        max_length=50, required=True,
        label='Номер лицензии/сертификата',
        widget=forms.TextInput(attrs={'placeholder': 'ВЛ-123456'}),
    )
    experience = forms.IntegerField(
        required=True, label='Стаж работы (лет)',
        min_value=0, max_value=60,
    )
    clinic = forms.CharField(
        max_length=200, required=True,
        label='Место работы (клиника)',
        widget=forms.TextInput(attrs={'placeholder': 'ВетОракул'}),
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'middle_name', 'phone', 'city')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)

        for name, field in self.fields.items():
            if name == 'specialization':
                field.widget.attrs.update({'class': 'form-input form-select'})
            else:
                field.widget.attrs.update({'class': 'form-input'})

        # Плейсхолдеры — как в образце
        self.fields['last_name'].widget.attrs['placeholder'] = 'Иванов'
        self.fields['first_name'].widget.attrs['placeholder'] = 'Иван'
        self.fields['middle_name'].widget.attrs['placeholder'] = 'Иванович'
        self.fields['email'].widget.attrs['placeholder'] = 'doctor@vetoracul.ru'
        self.fields['phone'].widget.attrs['placeholder'] = '+7 (___) ___-__-__'
        self.fields['city'].widget.attrs['placeholder'] = 'Москва'
        self.fields['education'].widget.attrs['placeholder'] = 'МГАВМиБ им. Скрябина'
        self.fields['grad_year'].widget.attrs['placeholder'] = '2015'
        self.fields['license_number'].widget.attrs['placeholder'] = 'ВЛ-123456'
        self.fields['experience'].widget.attrs['placeholder'] = '5'
        self.fields['clinic'].widget.attrs['placeholder'] = 'ВетОракул'
        self.fields['password1'].widget.attrs['placeholder'] = 'Минимум 8 символов'
        self.fields['password2'].widget.attrs['placeholder'] = 'Повторите пароль'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        existing = User.objects.filter(email__iexact=email).first()
        if existing and existing.is_active:
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def save(self, commit=True):
        email = self.cleaned_data['email']
        existing = User.objects.filter(email__iexact=email, is_active=False).first()

        if existing:
            user = existing
        else:
            user = super().save(commit=False)
            base = email.split('@')[0]
            username = base
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f'{base}{counter}'
                counter += 1
            user.username = username

        user.role = 'vet'
        user.is_active = False
        user.email = email
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.middle_name = self.cleaned_data.get('middle_name', '')
        user.phone = self.cleaned_data['phone']
        user.city = self.cleaned_data.get('city', '')
        user.set_password(self.cleaned_data['password1'])
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
        fields = ('diagnosis_text', 'treatment', 'date', 'status')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Текущее состояние питомца как начальное значение
        if self.instance and self.instance.pk and self.instance.pet_id:
            self.fields['new_health_status'].initial = self.instance.pet.health_status

        apply_input_classes(self.fields, select_fields={'status'})
        self.fields['treatment'].required = False

        # Ветеринар видит поле «Врач» только если редактирует чужой диагноз
        # (в остальных случаях vet проставляется автоматически)
        if self.user and self.user.role == 'vet' and self.instance and self.instance.pk:
            self.fields['vet'] = forms.ModelChoiceField(
                queryset=User.objects.filter(role='vet'),
                required=False,
                label='Ветеринар',
                widget=forms.Select(attrs={'class': 'form-input form-select'}),
            )
            if self.instance.vet_id:
                self.fields['vet'].initial = self.instance.vet_id
        elif self.user and self.user.role == 'vet':
            # Всё равно даём опцию сменить врача при создании, если нужно —
            # но по умолчанию подставим себя в view. Поле скрыто.
            pass

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
        fields = ('first_name', 'last_name', 'middle_name', 'email', 'phone', 'city', 'photo')

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
        fields = (
            'notify_email',
            'notify_appointments',
            'notify_vaccinations',
            'notify_urgent',
        )
        
class ResendCodeByEmailForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'example@mail.ru'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email__iexact=email, is_active=False)
        except User.DoesNotExist:
            raise forms.ValidationError('Активный аккаунт с таким email не найден или уже подтверждён.')
        self.user = user
        return email
    

# =========================================================
# Профиль ветеринара (User + VetProfile)
# =========================================================
class VetUserForm(forms.ModelForm):
    """Личные данные ветеринара (модель User)."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'middle_name', 'email', 'phone', 'city', 'photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'photo':
                continue
            field.widget.attrs.update({'class': 'form-input'})
        self.fields['photo'].required = False
        self.fields['middle_name'].required = False
        self.fields['city'].required = False

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Этот email уже занят.')
        return email


class VetProfileInfoForm(forms.ModelForm):
    """Профессиональные данные ветеринара (модель VetProfile)."""
    class Meta:
        model = VetProfile
        fields = (
            'specialization', 'education', 'grad_year',
            'license_number', 'experience', 'clinic',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_input_classes(self.fields, select_fields={'specialization'})