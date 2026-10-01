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
    
    photo = models.ImageField(
        upload_to='users/%Y/%m/%d/',
        blank=True, null=True,
        verbose_name='Фото профиля'
    )

    # Настройки уведомлений
    notify_appointments = models.BooleanField(default=True, verbose_name='Записи на приём')
    notify_vaccinations = models.BooleanField(default=True, verbose_name='Напоминания о вакцинации')
    notify_urgent = models.BooleanField(default=True, verbose_name='Срочные случаи')
    notify_news = models.BooleanField(default=False, verbose_name='Новости и обновления')

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

    class HealthStatus(models.TextChoices):
        HEALTHY = 'healthy', 'Здоров'
        OBSERVATION = 'observation', 'Под наблюдением'
        TREATMENT = 'treatment', 'На лечении'
        RECOVERY = 'recovery', 'Восстановление'
        CHRONIC = 'chronic', 'Хроническое заболевание'
        CRITICAL = 'critical', 'Критическое состояние'
        QUARANTINE = 'quarantine', 'Карантин'

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='pets', verbose_name='Владелец'
    )
    co_owners = models.ManyToManyField(
        User,
        through='PetCoOwner',
        related_name='co_owned_pets',
        blank=True,
        verbose_name='Совладельцы'
    )
    name = models.CharField(max_length=100, verbose_name='Кличка')
    animal_type = models.CharField(max_length=50, verbose_name='Вид животного')

    # --- НОВОЕ ---
    breed = models.CharField(
        max_length=100, blank=True,
        verbose_name='Порода'
    )
    photo = models.ImageField(
        upload_to='pets/%Y/%m/%d/',
        blank=True, null=True,
        verbose_name='Фото'
    )
    health_status = models.CharField(
        max_length=20,
        choices=HealthStatus.choices,
        default=HealthStatus.HEALTHY,
        verbose_name='Состояние здоровья'
    )
    
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Особые заметки'
    )

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='Пол')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    weight = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Вес (кг)'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Питомец'
        verbose_name_plural = 'Питомцы'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (владелец: {self.owner.get_full_name()})'

        # --- Права доступа ---
    def is_owner(self, user):
        return user.is_authenticated and self.owner_id == user.id

    def is_co_owner(self, user):
        if not user.is_authenticated:
            return False
        return self.co_owner_links.filter(user=user).exists()

    def co_owner_access_level(self, user):
        """Возвращает 'read' / 'write' / None."""
        if not user.is_authenticated:
            return None
        link = self.co_owner_links.filter(user=user).first()
        return link.access_level if link else None

    def can_view(self, user):
        if not user.is_authenticated:
            return False
        if user.role == 'vet':
            return True
        return self.is_owner(user) or self.is_co_owner(user)

    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        if user.role == 'vet':
            return True
        if self.is_owner(user):
            return True
        return self.co_owner_links.filter(
            user=user, access_level=PetCoOwner.AccessLevel.WRITE
        ).exists()

    def can_delete(self, user):
        """Удалять может только владелец."""
        return self.is_owner(user)
    
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

    # --- НОВОЕ: css-класс для бейджа состояния ---
    @property
    def health_status_class(self):
        return {
            'healthy': 'status-active',
            'observation': 'status-warning',
            'treatment': 'status-treatment',
            'recovery': 'status-recovery',
            'chronic': 'status-chronic',
            'critical': 'status-critical',
            'quarantine': 'status-inactive',
        }.get(self.health_status, 'status-active')


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
    treatment = models.TextField(
        blank=True,
        verbose_name='Прописанное лечение'
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
    

class Folder(models.Model):
    """
    Папка для организации документов в личном кабинете пользователя.
    Поддерживает вложенность через self-FK.
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='folders',
        verbose_name='Владелец'
    )
    name = models.CharField(max_length=200, verbose_name='Название папки')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительская папка'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Папка'
        verbose_name_plural = 'Папки'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'parent', 'name'],
                name='unique_folder_per_parent'
            )
        ]

    def __str__(self):
        return self.name

    @property
    def is_root(self):
        return self.parent is None


class Document(models.Model):
    """Модель загруженного документа, привязанного к питомцу."""
    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Питомец'
    )
    folder = models.ForeignKey(
        Folder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name='Папка'
    )
    file = models.FileField(upload_to='documents/%Y/%m/%d/', verbose_name='Файл')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
        verbose_name='Кем загружен'
    )
    date = models.DateField(verbose_name='Дата документа')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    title = models.CharField(max_length=255, blank=True, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')

    is_deleted = models.BooleanField(default=False, verbose_name='Удалён', db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата удаления')
    
    share_token = models.UUIDField(
        null=True, blank=True, unique=True, db_index=True,
        verbose_name='Токен публичной ссылки'
    )
    is_public = models.BooleanField(default=False, verbose_name='Публичный доступ')

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['date']

    def __str__(self):
        return f'Документ от {self.date} для {self.pet.name}'

    def soft_delete(self):
        """Помечает документ удалённым, не удаляя файл с диска."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Восстанавливает документ из корзины."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])


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
    notified_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Когда отправлено уведомление',
        db_index=True
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
    
class PetCoOwner(models.Model):
    """Связь питомца с совладельцем и его уровнем доступа."""
    class AccessLevel(models.TextChoices):
        READ = 'read', 'Только просмотр'
        WRITE = 'write', 'Полный доступ'

    pet = models.ForeignKey(
        Pet, on_delete=models.CASCADE,
        related_name='co_owner_links',
        verbose_name='Питомец'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='co_owned_pet_links',
        verbose_name='Совладелец'
    )
    access_level = models.CharField(
        max_length=10,
        choices=AccessLevel.choices,
        default=AccessLevel.READ,
        verbose_name='Уровень доступа'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Совладелец'
        verbose_name_plural = 'Совладельцы'
        unique_together = ('pet', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} → {self.pet.name} ({self.get_access_level_display()})'