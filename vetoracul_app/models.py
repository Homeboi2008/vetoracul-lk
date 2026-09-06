import random
import string
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth import get_user_model


class User(AbstractUser):
    """Расширенная модель пользователя с ролями и контактными данными."""
    ROLE_CHOICES = (
        ('user', 'Пользователь'),
        ('vet', 'Ветеринар'),
    )

    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name='Роль'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Номер телефона'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Город проживания'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.get_full_name() or self.username

    def has_active_subscription(self):
        if self.role == 'vet':
            return True
        return self.subscriptions.filter(
            is_active=True,
            end_date__gte=timezone.now().date()
        ).exists()


class Pet(models.Model):
    GENDER_CHOICES = (
        ('M', 'Мужской'),
        ('F', 'Женский'),
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pets',
        verbose_name='Владелец'
    )
    co_owners = models.ManyToManyField(
        User,
        related_name='co_owned_pets',
        blank=True,
        verbose_name='Совладельцы'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Кличка'
    )
    animal_type = models.CharField(
        max_length=50,
        verbose_name='Вид животного'
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name='Пол'
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Вес (кг)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Питомец'
        verbose_name_plural = 'Питомцы'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (владелец: {self.owner.get_full_name()})'

    @property
    def age(self):
        if self.birth_date:
            today = timezone.now().date()
            age = today.year - self.birth_date.year
            if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
                age -= 1
            return age
        return None

    @property
    def current_diagnosis(self):
        last = self.diagnoses.order_by('-date').first()
        return last.diagnosis_text if last else None


class Diagnosis(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активный'
        IMPROVING = 'improving', 'Улучшается'
        STABLE = 'stable', 'Стабильный'
        WORSENING = 'worsening', 'Ухудшается'
        RESOLVED = 'resolved', 'Излечен'
        REMISSION = 'remission', 'Ремиссия'
        CHRONIC = 'chronic', 'Хронический'
        RECURRING = 'recurring', 'Рецидивирующий'
        SUSPECT = 'suspect', 'Под вопросом'
        INACTIVE = 'inactive', 'Неактивный'

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='diagnoses',
        verbose_name='Питомец'
    )
    diagnosis_text = models.TextField(
        verbose_name='Диагноз'
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name='Дата постановки диагноза'
    )
    vet = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'vet'},
        verbose_name='Ветеринар, поставивший диагноз'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания записи'
    )

    class Meta:
        verbose_name = 'Диагноз'
        verbose_name_plural = 'Диагнозы'
        ordering = ['-date']

    def __str__(self):
        return f'{self.pet.name}: {self.diagnosis_text[:30]}... ({self.date})'


class Document(models.Model):
    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Питомец'
    )
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        verbose_name='Файл'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
        verbose_name='Кем загружен'
    )
    date = models.DateField(
        verbose_name='Дата документа'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата загрузки'
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Название'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['date']

    def __str__(self):
        return f'Документ от {self.date} для {self.pet.name}'


class Reminder(models.Model):
    class Type(models.TextChoices):
        CHECKUP = 'checkup', 'Осмотр'
        VACCINATION = 'vaccination', 'Прививка'
        INJECTION = 'injection', 'Укол'
        MEDICATION = 'medication', 'Приём лекарств'
        GROOMING = 'grooming', 'Груминг'
        SURGERY = 'surgery', 'Операция'
        OTHER = 'other', 'Другое'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает'
        COMPLETED = 'completed', 'Выполнено'
        MISSED = 'missed', 'Пропущено'
        CANCELLED = 'cancelled', 'Отменено'

    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name='Питомец'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Заголовок'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.OTHER,
        verbose_name='Тип напоминания'
    )
    date = models.DateField(
        verbose_name='Дата'
    )
    time = models.TimeField(
        blank=True,
        null=True,
        verbose_name='Время (опционально)'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reminders',
        verbose_name='Кем создано'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Напоминание'
        verbose_name_plural = 'Напоминания'
        ordering = ['date', 'time']

    def __str__(self):
        return f'{self.title} для {self.pet.name} ({self.date})'

    @property
    def is_past(self):
        return self.date < timezone.now().date()

    @property
    def is_today(self):
        return self.date == timezone.now().date()


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активна'
        EXPIRED = 'expired', 'Истекла'
        CANCELLED = 'cancelled', 'Отменена'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Пользователь',
        limit_choices_to={'role': 'user'}
    )
    start_date = models.DateField(
        default=timezone.now,
        verbose_name='Дата начала'
    )
    end_date = models.DateField(
        verbose_name='Дата окончания'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name='Статус'
    )
    payment_amount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=200.00,
        verbose_name='Сумма оплаты'
    )
    payment_method = models.CharField(
        max_length=20,
        default='sbp',
        verbose_name='Способ оплаты'
    )
    payment_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='ID платежа (внешняя система)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-start_date']

    def __str__(self):
        return f'Подписка {self.user.username} ({self.start_date} - {self.end_date})'

    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=30)
        if self.is_active and self.end_date < timezone.now().date():
            self.is_active = False
            self.status = Status.EXPIRED
        super().save(*args, **kwargs)

    @property
    def days_left(self):
        delta = self.end_date - timezone.now().date()
        return delta.days
    

User = get_user_model()

class EmailVerificationCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_code')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = ''.join(random.choices(string.digits, k=6))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"{self.user.email} – {self.code}"