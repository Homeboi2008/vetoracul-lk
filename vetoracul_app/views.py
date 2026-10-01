import logging
logger = logging.getLogger(__name__)

from datetime import timedelta

from django.views.generic import TemplateView, View, CreateView, FormView, ListView, UpdateView, DeleteView, DetailView
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView
from django.contrib.auth import login
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q

from .models import Subscription, EmailVerificationCode, User, Pet, Reminder, Folder, Document, VetAccess, VetAccessRequest
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordResetForm, CustomSetPasswordForm, VerificationCodeForm, PetForm, FolderForm, DocumentUploadForm, VetRegistrationForm

from datetime import timedelta


def _send_pending_reminder_notifications(user=None):
    """
    Отправляет email-уведомления о напоминаниях, которые наступают завтра.
    Учитывает пользовательские настройки: notify_appointments, notify_vaccinations.
    Повторно не отправляет — использует поле notified_at.
    """
    from datetime import timedelta
    tomorrow = timezone.now().date() + timedelta(days=1)

    qs = Reminder.objects.filter(
        status=Reminder.Status.PENDING,
        date=tomorrow,
        notified_at__isnull=True,
    ).select_related('pet', 'pet__owner')

    if user is not None:
        qs = qs.filter(pet__owner=user)

    sent = 0
    for r in qs:
        owner = r.pet.owner

        # --- Проверка настроек уведомлений ---
        # Вакцинация / укол — управляется notify_vaccinations
        if r.reminder_type in (Reminder.Type.VACCINATION, Reminder.Type.INJECTION):
            if not owner.notify_vaccinations:
                continue
        # Осмотр / операция — управляется notify_appointments
        elif r.reminder_type in (Reminder.Type.CHECKUP, Reminder.Type.SURGERY):
            if not owner.notify_appointments:
                continue
        # Остальные типы (medication, grooming, other) — отправляем всегда

        recipients = []
        if owner.email:
            recipients.append(owner.email)
        for co in r.pet.co_owners.all():
            if co.email:
                recipients.append(co.email)

        if not recipients:
            continue

        time_str = f' в {r.time.strftime("%H:%M")}' if r.time else ''
        subject = f'Напоминание: {r.title} — завтра'
        message = (
            f'Здравствуйте!\n\n'
            f'Напоминаем, что завтра, {r.date.strftime("%d.%m.%Y")}{time_str}, '
            f'у питомца {r.pet.name} запланировано:\n\n'
            f'• {r.title}\n'
            f'  Тип: {r.get_reminder_type_display()}\n'
            + (f'  Описание: {r.description}\n' if r.description else '') +
            f'\nНе забудьте!\n\n— ВетОракул'
        )

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
            r.notified_at = timezone.now()
            r.save(update_fields=['notified_at'])
            sent += 1
        except Exception as e:
            logger.error('Не удалось отправить уведомление #%s: %s', r.pk, e)

    return sent


class SubscriptionView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Страница управления подпиской.
    Доступна только обычным пользователям (не ветеринарам).
    """
    template_name = 'subscription.html'

    def test_func(self):
        return self.request.user.role == 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Берём первую активную подписку (по задумке она должна быть одна, но может быть несколько)
        active_sub = user.subscriptions.filter(is_active=True).first()
        context['active_subscription'] = active_sub
        return context


class CreateSubscriptionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Обработчик оплаты подписки.
    Если активная подписка есть – продлевает её на 30 дней.
    Если нет – создаёт новую с началом сегодня.
    """
    def test_func(self):
        return self.request.user.role == 'user'

    def post(self, request, *args, **kwargs):
        user = request.user
        active_sub = user.subscriptions.filter(is_active=True).first()

        if active_sub:
            # Продлеваем существующую подписку
            active_sub.end_date += timedelta(days=30)
            active_sub.save()
            messages.success(request, f'Подписка продлена до {active_sub.end_date}.')
        else:
            # Создаём новую подписку
            start_date = timezone.now().date()
            end_date = start_date + timedelta(days=30)
            Subscription.objects.create(
                user=user,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                status=Subscription.Status.ACTIVE,
                payment_amount=200.00,
                payment_method='sbp',                 # СБП
                payment_id=f'mock_{int(timezone.now().timestamp())}',  # заглушка ID платежа
            )
            messages.success(request, f'Подписка оформлена до {end_date}.')

        return redirect('subscription')  # имя URL-маршрута для страницы подписки
    

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'auth/register.html'
    success_url = reverse_lazy('verify_email')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False  # аккаунт не активен до подтверждения
        user.save()
        # Создаём код верификации
        code_obj = EmailVerificationCode.objects.create(user=user)
        # Отправляем письмо
        self.send_verification_email(user, code_obj.code)
        # Сохраняем ID пользователя в сессии для последующего подтверждения
        self.request.session['pending_user_id'] = user.id
        messages.success(self.request, 'На ваш email отправлен код подтверждения.')
        return super().form_valid(form)

    def send_verification_email(self, user, code):
        subject = 'Подтверждение регистрации в ВетКлинике'
        message = f'Здравствуйте, {user.username}!\n\nВаш код подтверждения: {code}\n\nКод действителен 15 минут.'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.POST.get('remember_me'):
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(1209600)
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Неверный email/логин или пароль.')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = 'login'


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html'
    subject_template_name = 'auth/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
        logger.warning('>>> Начинаю отправку письма для %s', form.cleaned_data['email'])
        response = super().form_valid(form)
        logger.warning('>>> Письмо успешно отправлено')
        return response


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class ProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return redirect(reverse('home') + '#settings')

class VerifyEmailView(FormView):
    form_class = VerificationCodeForm
    template_name = 'auth/verify_email.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('pending_user_id'):
            messages.error(request, 'Сессия истекла. Зарегистрируйтесь заново.')
            return redirect('register')
        self.user_id = request.session['pending_user_id']
        self.user = get_object_or_404(User, id=self.user_id, is_active=False)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def form_valid(self, form):
        # Код верен – активируем пользователя
        self.user.is_active = True
        self.user.save()
        # Удаляем код
        EmailVerificationCode.objects.filter(user=self.user).delete()

        # 👇 ВАЖНО: указываем backend явно, т.к. их несколько
        self.user.backend = 'django.contrib.auth.backends.ModelBackend'

        # Автоматически логиним пользователя
        login(self.request, self.user)
        messages.success(self.request, 'Ваш email подтверждён! Добро пожаловать.')
        del self.request.session['pending_user_id']
        return super().form_valid(form)

class ResendCodeView(View):
    def post(self, request):
        user_id = request.session.get('pending_user_id')
        if not user_id:
            messages.error(request, 'Сессия истекла. Зарегистрируйтесь заново.')
            return redirect('register')
        user = get_object_or_404(User, id=user_id, is_active=False)
        # Удаляем старый код, генерируем новый
        EmailVerificationCode.objects.filter(user=user).delete()
        new_code = EmailVerificationCode.objects.create(user=user)
        # Отправляем письмо повторно
        subject = 'Новый код подтверждения'
        message = f'Здравствуйте, {user.username}!\n\nВаш новый код: {new_code.code}'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        messages.success(request, 'Новый код отправлен на ваш email.')
        return redirect('verify_email')
    




# ---------- Папки ----------

class FolderListView(LoginRequiredMixin, ListView):
    """Список папок пользователя (личный кабинет)."""
    model = Folder
    template_name = 'cabinet/folder_list.html'
    context_object_name = 'folders'

    def get_queryset(self):
        return Folder.objects.filter(owner=self.request.user, parent__isnull=True)


class FolderCreateView(LoginRequiredMixin, CreateView):
    model = Folder
    form_class = FolderForm
    template_name = 'cabinet/folder_form.html'
    success_url = reverse_lazy('home')   # ← было folder_list

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['owner'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        # parent берём из POST (скрытое поле модалки)
        parent_id = self.request.POST.get('parent', '').strip()
        if parent_id:
            try:
                form.instance.parent = Folder.objects.get(pk=parent_id, owner=self.request.user)
            except Folder.DoesNotExist:
                pass
        messages.success(self.request, 'Папка создана.')
        return super().form_valid(form)


class FolderUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Folder
    form_class = FolderForm
    template_name = 'cabinet/folder_form.html'
    success_url = reverse_lazy('folder_list')

    def test_func(self):
        return self.get_object().owner == self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['owner'] = self.request.user
        return kwargs


class FolderDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Folder
    template_name = 'cabinet/folder_confirm_delete.html'

    def test_func(self):
        return self.get_object().owner == self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Папка удалена.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('home') + '#documents'


class FolderDetailView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Просмотр содержимого папки: подпапки + документы."""
    template_name = 'cabinet/folder_detail.html'
    context_object_name = 'documents'

    def test_func(self):
        return self.get_object().owner == self.request.user

    def get_object(self):
        return get_object_or_404(Folder, pk=self.kwargs['pk'], owner=self.request.user)

    def get_queryset(self):
        return Document.objects.filter(
            folder=self.get_object(), is_deleted=False
        ).order_by('-date')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['folder'] = self.get_object()
        ctx['subfolders'] = self.get_object().children.all()
        return ctx


# ---------- Документы ----------

class DocumentUploadView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentUploadForm
    template_name = 'cabinet/document_upload.html'

    def dispatch(self, request, *args, **kwargs):
        self.pet = get_object_or_404(Pet, pk=kwargs['pet_pk'])
        # Проверка доступа: владелец или совладелец или ветеринар
        if not self.pet.can_edit(request.user):
            messages.error(request, 'Нет доступа к этому питомцу.')
            return redirect('folder_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.pet = self.pet
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Документ загружен.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('folder_list')


# ---------- Корзина ----------

class TrashListView(LoginRequiredMixin, ListView):
    """Список удалённых документов пользователя (только его питомцев)."""
    model = Document
    template_name = 'cabinet/trash.html'
    context_object_name = 'documents'

    def get_queryset(self):
        # Документы питомцев, где пользователь — владелец или совладелец
        return Document.objects.filter(
            is_deleted=True,
            pet__owner=self.request.user
        ) | Document.objects.filter(
            is_deleted=True,
            pet__co_owners=self.request.user
        )


class DocumentRestoreView(LoginRequiredMixin, View):
    def post(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if not (doc.pet.owner == request.user or request.user in doc.pet.co_owners.all()):
            messages.error(request, 'Нет доступа.')
            return redirect('home')
        doc.restore()
        messages.success(request, 'Документ восстановлен.')
        return redirect('home')


class DocumentPermanentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if not (doc.pet.owner == request.user or request.user in doc.pet.co_owners.all()):
            messages.error(request, 'Нет доступа.')
            return redirect('home')
        doc.file.delete(save=False)
        doc.delete()
        messages.success(self.request, 'Документ удалён безвозвратно.')
        return redirect('home')
    

class DocumentSoftDeleteView(LoginRequiredMixin, View):
    """Обычное удаление — отправка в корзину."""
    def post(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if not (doc.pet.owner == request.user or request.user in doc.pet.co_owners.all()):
            messages.error(request, 'Нет доступа.')
            return redirect('home')
        doc.soft_delete()
        messages.success(request, 'Документ перемещён в корзину.')
        return redirect('home')

class PetListView(LoginRequiredMixin, ListView):
    """Список питомцев пользователя (свои + где он совладелец)."""
    model = Pet
    template_name = 'pets/pet_list.html'
    context_object_name = 'pets'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'vet':
            return Pet.objects.all().order_by('name')
        return Pet.objects.filter(
            Q(owner=user) | Q(co_owners=user)
        ).distinct().order_by('name')


class PetCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Pet
    form_class = PetForm
    template_name = 'pets/pet_form.html'
    success_url = reverse_lazy('pet_list')

    def test_func(self):
        # Только обычные пользователи могут добавлять питомцев
        return self.request.user.role == 'user'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f'Питомец «{form.instance.name}» добавлен.')
        return super().form_valid(form)


class PetDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Pet
    template_name = 'pets/pet_detail.html'
    context_object_name = 'pet'

    def test_func(self):
        return self.get_object().can_view(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pet = self.get_object()
        ctx['diagnoses'] = pet.diagnoses.order_by('-date')
        ctx['documents'] = pet.documents.filter(is_deleted=False).order_by('-date')
        ctx['reminders'] = pet.reminders.order_by('date', 'time')
        ctx['can_edit'] = pet.can_edit(self.request.user)
        return ctx


class PetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Pet
    form_class = PetForm
    template_name = 'pets/pet_form.html'
    success_url = reverse_lazy('pet_list')

    def test_func(self):
        return self.get_object().can_edit(self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Данные питомца обновлены.')
        return super().form_valid(form)


class PetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Pet
    template_name = 'pets/pet_confirm_delete.html'
    success_url = reverse_lazy('pet_list')

    def test_func(self):
        return self.get_object().can_delete(self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Питомец удалён.')
        return super().form_valid(form)
    

from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import Pet, Diagnosis, Document, Reminder
from .forms import DiagnosisForm, DocumentForm, ReminderForm


class PetAccessMixin(LoginRequiredMixin):
    """Проверяет доступ к питомцу.
    Атрибут required_access = 'view' | 'edit' (по умолчанию 'edit')."""

    required_access = 'edit'

    def get_pet(self):
        pet = get_object_or_404(Pet, pk=self.kwargs['pet_pk'])
        user = self.request.user
        allowed = pet.can_view(user) if self.required_access == 'view' else pet.can_edit(user)
        if not allowed:
            messages.error(self.request, 'Недостаточно прав для этого действия.')
            return None
        return pet

    def dispatch(self, request, *args, **kwargs):
        self.pet = self.get_pet()
        if self.pet is None:
            return redirect('pet_list')
        return super().dispatch(request, *args, **kwargs)

# ---------- ДИАГНОЗЫ ----------

class DiagnosisCreateView(PetAccessMixin, CreateView):
    model = Diagnosis
    form_class = DiagnosisForm
    template_name = 'pets/diagnosis_form.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['new_health_status'] = self.pet.health_status
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.pet = self.pet

        # Автоподстановка врача
        if self.request.user.role == 'vet':
            form.instance.vet = self.request.user

        # Обновление состояния питомца
        new_status = form.cleaned_data.get('new_health_status')
        if new_status and new_status != self.pet.health_status:
            self.pet.health_status = new_status
            self.pet.save(update_fields=['health_status'])

        messages.success(self.request, 'Диагноз добавлен.')
        return super().form_valid(form)

    def get_success_url(self):
        if self.request.user.role == 'vet':
            return reverse_lazy('vet_patient_card', kwargs={'pk': self.pet.pk})
        return reverse_lazy('pet_detail', kwargs={'pk': self.pet.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pet'] = self.pet
        ctx['title'] = 'Добавить диагноз'
        return ctx


class DiagnosisUpdateView(LoginRequiredMixin, UpdateView):
    model = Diagnosis
    form_class = DiagnosisForm
    template_name = 'pets/diagnosis_form.html'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'vet':
            return Diagnosis.objects.filter(vet=user)
        return Diagnosis.objects.filter(
            Q(pet__owner=user) | Q(pet__co_owners=user)
        ).distinct()

    def get_initial(self):
        initial = super().get_initial()
        if self.object and self.object.pet:
            initial['new_health_status'] = self.object.pet.health_status
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Если врач не менял поле vet (или оно недоступно), оставляем как было
        if self.request.user.role == 'vet' and 'vet' not in form.cleaned_data:
            form.instance.vet = self.request.user

        new_status = form.cleaned_data.get('new_health_status')
        pet = self.object.pet
        if new_status and new_status != pet.health_status:
            pet.health_status = new_status
            pet.save(update_fields=['health_status'])

        messages.success(self.request, 'Диагноз обновлён.')
        return super().form_valid(form)

    def get_success_url(self):
        if self.request.user.role == 'vet':
            return reverse_lazy('vet_patient_card', kwargs={'pk': self.object.pet.pk})
        return reverse_lazy('pet_detail', kwargs={'pk': self.object.pet.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pet'] = self.object.pet
        ctx['title'] = 'Редактировать диагноз'
        return ctx


class DiagnosisDeleteView(LoginRequiredMixin, DeleteView):
    model = Diagnosis
    template_name = 'pets/confirm_delete.html'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'vet':
            return Diagnosis.objects.all()
        return Diagnosis.objects.filter(
            Q(pet__owner=user)
            | Q(pet__co_owner_links__user=user, pet__co_owner_links__access_level='write')
        ).distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['object_type'] = 'диагноз'
        ctx['cancel_url'] = reverse_lazy('pet_detail', kwargs={'pk': self.object.pet.pk})
        return ctx

    def get_success_url(self):
        return reverse_lazy('pet_detail', kwargs={'pk': self.object.pet.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Диагноз удалён.')
        return super().form_valid(form)


# ---------- ДОКУМЕНТЫ ----------

class DocumentCreateView(PetAccessMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'pets/document_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.pet = self.pet
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Документ загружен.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pet'] = self.pet
        ctx['title'] = 'Загрузить документ'
        return ctx
    
    def get_success_url(self):
        return reverse_lazy('home') + '#documents'


class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'pets/document_form.html'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'vet':
            return Diagnosis.objects.all()
        return Diagnosis.objects.filter(
            Q(pet__owner=user)
            | Q(pet__co_owner_links__user=user, pet__co_owner_links__access_level='write')
        ).distinct()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Документ обновлён.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('pet_detail', kwargs={'pk': self.object.pet.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pet'] = self.object.pet
        ctx['title'] = 'Редактировать документ'
        return ctx


# ---------- НАПОМИНАНИЯ ----------

class ReminderCreateView(PetAccessMixin, CreateView):
    model = Reminder
    form_class = ReminderForm
    template_name = 'pets/reminder_form.html'

    def form_valid(self, form):
        form.instance.pet = self.pet
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Напоминание добавлено.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('home') + '#reminders'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pet'] = self.pet
        ctx['title'] = 'Добавить напоминание'
        return ctx


class ReminderUpdateView(LoginRequiredMixin, UpdateView):
    model = Reminder
    form_class = ReminderForm
    template_name = 'pets/reminder_form.html'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'vet':
            return Diagnosis.objects.all()
        return Diagnosis.objects.filter(
            Q(pet__owner=user)
            | Q(pet__co_owner_links__user=user, pet__co_owner_links__access_level='write')
        ).distinct()

    def form_valid(self, form):
        messages.success(self.request, 'Напоминание обновлено.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('home') + '#reminders'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pet'] = self.object.pet
        ctx['title'] = 'Редактировать напоминание'
        return ctx


class ReminderDeleteView(LoginRequiredMixin, DeleteView):
    model = Reminder
    template_name = 'pets/confirm_delete.html'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'vet':
            return Diagnosis.objects.all()
        return Diagnosis.objects.filter(
            Q(pet__owner=user)
            | Q(pet__co_owner_links__user=user, pet__co_owner_links__access_level='write')
        ).distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['object_type'] = 'напоминание'
        ctx['cancel_url'] = reverse('home') + '#reminders'
        return ctx

    def get_success_url(self):
        return reverse('home') + '#reminders'

    def form_valid(self, form):
        messages.success(self.request, 'Напоминание удалено.')
        return super().form_valid(form)
    
class VetDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'vet/dashboard.html'

    def test_func(self):
        return self.request.user.role == 'vet'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        accesses = VetAccess.objects.filter(vet=self.request.user).select_related('pet', 'pet__owner')
        ctx['accesses'] = accesses
        ctx['patients'] = [a.pet for a in accesses]
        ctx['patients_count'] = len(ctx['patients'])
        ctx['today'] = timezone.now().date()
        ctx['today_reminders'] = Reminder.objects.filter(
            pet__in=ctx['patients'],
            date=timezone.now().date(),
            status='pending'
        ).select_related('pet', 'pet__owner')
        return ctx
    
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def home_view(request):
    """Главная страница пользователя. Ветеринар редиректится в свой кабинет."""
    if request.user.role == 'vet':
        return redirect('vet_dashboard')

    user = request.user
    pets = (user.pets.all() | user.co_owned_pets.all()).distinct().order_by('name')

    documents = Document.objects.filter(pet__in=pets, is_deleted=False).order_by('-date')
    deleted_documents = Document.objects.filter(pet__in=pets, is_deleted=True).order_by('-deleted_at')
    reminders = Reminder.objects.filter(pet__in=pets).order_by('date', 'time')
    folders = Folder.objects.filter(owner=user).order_by('name')

    stats = {
        'pets': pets.count(),
        'documents': documents.count(),
        'reminders': reminders.filter(status=Reminder.Status.PENDING).count(),
    }

    pets_filter = [{'id': p.id, 'name': p.name} for p in pets]

    # Для удобства JS: список папок и parent_id
    folders_json = [
        {
            'id': f.id,
            'name': f.name,
            'parent_id': f.parent_id,
            'documents_count': f.documents.filter(is_deleted=False).count(),
        }
        for f in folders
    ]

    reminders_json = [
        {
            'id': r.id,
            'title': r.title,
            'date': r.date.isoformat(),
            'time': r.time.strftime('%H:%M') if r.time else '',
            'pet_name': r.pet.name,
            'type': r.reminder_type,
            'type_display': r.get_reminder_type_display(),
            'status': r.status,
            'status_display': r.get_status_display(),
            'description': r.description or '',
        }
        for r in reminders
    ]
    
    profile_form = UserProfileForm(instance=user)
    notification_form = NotificationSettingsForm(instance=user)

    # === Уведомления ===
    # 1. Заявки ветеринаров на доступ к питомцам пользователя
    pending_vet_requests = VetAccessRequest.objects.filter(
        pet__owner=user, status='pending'
    ).select_related('vet', 'pet').order_by('-created_at')

    # 2. Прошедшие напоминания с незакрытым статусом
    past_pending_reminders = Reminder.objects.filter(
        pet__in=pets,
        status=Reminder.Status.PENDING,
        date__lt=timezone.now().date(),
    ).select_related('pet').order_by('-date')[:20]

    notifications_count = pending_vet_requests.count() + past_pending_reminders.count()

    context = {
        'pets': pets,
        'documents': documents,
        'deleted_documents': deleted_documents,
        'reminders': reminders,
        'stats': stats,
        'pets_filter': pets_filter,
        'folders': folders,
        'folders_json': folders_json,
        'reminders_json': reminders_json,
        'profile_form': profile_form,
        'notification_form': notification_form,
        'pending_vet_requests': pending_vet_requests,
        'past_pending_reminders': past_pending_reminders,
        'notifications_count': notifications_count,
    }
    return render(request, 'home.html', context)


@login_required
def document_move(request, pk):
    """POST — перемещает документ в папку (или из папки)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Только POST'}, status=405)

    doc = get_object_or_404(Document, pk=pk)
    user = request.user

    if not (doc.pet.owner == user or user in doc.pet.co_owners.all()):
        return JsonResponse({'error': 'Нет доступа'}, status=403)

    folder_id = request.POST.get('folder_id', '').strip()
    if folder_id:
        folder = get_object_or_404(Folder, pk=folder_id, owner=user)
        doc.folder = folder
    else:
        doc.folder = None
    doc.save(update_fields=['folder'])
    return JsonResponse({'ok': True})

    
class VetRegisterView(CreateView):
    form_class = VetRegistrationForm
    template_name = 'auth/register_vet.html'
    success_url = reverse_lazy('verify_email')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = 'vet'
        user.is_active = False
        user.save()
        code_obj = EmailVerificationCode.objects.create(user=user)
        send_mail(
            'Подтверждение регистрации ветеринара в ВетОракуле',
            f'Здравствуйте, {user.first_name}!\n\nВаш код подтверждения: {code_obj.code}\n\nКод действителен 15 минут.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        self.request.session['pending_user_id'] = user.id
        messages.success(self.request, 'На ваш email отправлен код подтверждения.')
        return super().form_valid(form)
    
class VetPatientCardView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Pet
    template_name = 'vet/patient_card.html'
    context_object_name = 'pet'

    def test_func(self):
        pet = self.get_object()
        return self.request.user.role == 'vet' and pet.can_view(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pet = self.get_object()
        user = self.request.user

        ctx['diagnoses'] = pet.diagnoses.order_by('-date')
        ctx['documents'] = pet.documents.filter(is_deleted=False).order_by('-date')
        ctx['reminders'] = pet.reminders.order_by('date', 'time')

        # Права
        ctx['can_edit'] = pet.can_edit(user)
        ctx['can_add'] = pet.can_add(user)

        # Уровень доступа
        access = VetAccess.objects.filter(vet=user, pet=pet).first()
        ctx['access'] = access
        ctx['access_level_display'] = access.get_access_level_display() if access else '—'

        return ctx
    
class VetMedicalRecordCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Diagnosis
    form_class = DiagnosisForm
    template_name = 'vet/medical_record.html'

    def test_func(self):
        return self.request.user.role == 'vet'

    def dispatch(self, request, *args, **kwargs):
        self.pet = get_object_or_404(Pet, pk=kwargs['pet_pk'])
        # Проверяем, что у ветеринара есть доступ
        if not self.pet.can_view(request.user):
            messages.error(request, 'Нет доступа к этому питомцу.')
            return redirect('vet_patient_search')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial['new_health_status'] = self.pet.health_status
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.pet = self.pet
        form.instance.vet = self.request.user  # ← всегда сам ветеринар

        new_status = form.cleaned_data.get('new_health_status')
        if new_status and new_status != self.pet.health_status:
            self.pet.health_status = new_status
            self.pet.save(update_fields=['health_status'])

        messages.success(self.request, 'Медицинская запись добавлена.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('vet_patient_card', kwargs={'pk': self.pet.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pet'] = self.pet
        return ctx
    
import uuid
from django.http import JsonResponse, FileResponse, Http404


@login_required
def document_share(request, pk):
    """POST — генерирует (или возвращает) публичную ссылку на документ."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Только POST'}, status=405)

    doc = get_object_or_404(Document, pk=pk)
    user = request.user

    # Проверка доступа
    if not (
        doc.pet.owner == user
        or user in doc.pet.co_owners.all()
        or user.role == 'vet'
    ):
        return JsonResponse({'error': 'Нет доступа'}, status=403)

    if doc.is_deleted:
        return JsonResponse({'error': 'Документ в корзине'}, status=400)

    if not doc.share_token or not doc.is_public:
        doc.share_token = uuid.uuid4()
        doc.is_public = True
        doc.save(update_fields=['share_token', 'is_public'])

    url = request.build_absolute_uri(
        reverse('document_public', kwargs={'token': str(doc.share_token)})
    )
    return JsonResponse({'url': url, 'token': str(doc.share_token)})


def document_public(request, token):
    """Публичный доступ к файлу документа по токену."""
    try:
        doc = Document.objects.get(share_token=token, is_public=True)
    except Document.DoesNotExist:
        raise Http404('Документ не найден или ссылка отозвана')

    if doc.is_deleted:
        raise Http404('Документ больше не доступен')

    if not doc.file:
        raise Http404('Файл отсутствует')

    # Отдаём файл как вложение (или inline — параметром)
    as_attachment = request.GET.get('download') == '1'
    return FileResponse(
        doc.file.open('rb'),
        as_attachment=as_attachment,
        filename=doc.file.name.split('/')[-1],
    )
    
@login_required
def document_unshare(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Только POST'}, status=405)
    doc = get_object_or_404(Document, pk=pk)
    user = request.user
    if not (doc.pet.owner == user or user in doc.pet.co_owners.all()):
        return JsonResponse({'error': 'Нет доступа'}, status=403)
    doc.is_public = False
    doc.share_token = None
    doc.save(update_fields=['is_public', 'share_token'])
    return JsonResponse({'ok': True})

@login_required
def user_search(request):
    """AJAX-поиск пользователей по email/имени для Select2."""
    q = request.GET.get('q', '').strip()
    qs = User.objects.filter(role='user').exclude(pk=request.user.pk)
    if q:
        qs = qs.filter(
            Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(username__icontains=q)
        )
    qs = qs.order_by('email')[:20]
    results = [
        {
            'id': u.pk,
            'text': f'{(u.get_full_name() or u.username)} — {u.email}',
            'email': u.email,
        }
        for u in qs
    ]
    return JsonResponse({'results': results})

from .forms import UserProfileForm, NotificationSettingsForm  # добавьте к существующим импортам


@login_required
def profile_update(request):
    """POST — обновление профиля и/или фото."""
    if request.method != 'POST':
        return redirect('home')
    form = UserProfileForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'Профиль обновлён.')
    else:
        for errors in form.errors.values():
            for e in errors:
                messages.error(request, e)
    return redirect(reverse('home') + '#settings')


@login_required
def profile_photo_delete(request):
    """POST — удалить фото профиля."""
    if request.method != 'POST':
        return redirect('home')
    if request.user.photo:
        request.user.photo.delete(save=True)
        messages.success(request, 'Фото профиля удалено.')
    return redirect(reverse('home') + '#settings')


@login_required
def notification_settings_update(request):
    """POST — сохранение настроек уведомлений."""
    if request.method != 'POST':
        return redirect('home')
    form = NotificationSettingsForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'Настройки уведомлений сохранены.')
    return redirect(reverse('home') + '#settings')


@login_required
def vet_patient_search(request):
    """Ветеринар ищет владельца по email."""
    if request.user.role != 'vet':
        return redirect('home')

    email_query = request.GET.get('email', '').strip()
    found_user = None
    pets = []

    if email_query:
        found_user = User.objects.filter(
            role='user', email__iexact=email_query
        ).first()
        if found_user:
            pets = Pet.objects.filter(owner=found_user).order_by('name')

    # Уже одобренные доступы и активные заявки
    existing_access = {}
    pending_requests = {}
    if found_user:
        for a in VetAccess.objects.filter(vet=request.user, pet__owner=found_user):
            existing_access[a.pet_id] = a.access_level
        for r in VetAccessRequest.objects.filter(
            vet=request.user, pet__owner=found_user, status='pending'
        ):
            pending_requests[r.pet_id] = r.access_level

    context = {
        'email_query': email_query,
        'found_user': found_user,
        'pets': pets,
        'existing_access': existing_access,
        'pending_requests': pending_requests,
    }
    return render(request, 'vet/patient_search.html', context)


@login_required
def vet_request_access(request, pet_pk):
    """POST — создать заявку на доступ к питомцу."""
    if request.user.role != 'vet':
        return redirect('home')
    if request.method != 'POST':
        return redirect('vet_patient_search')

    pet = get_object_or_404(Pet, pk=pet_pk)
    level = request.POST.get('access_level', 'view')
    if level not in dict(VetAccessRequest.AccessLevel.choices):
        level = 'view'

    # Уже есть доступ?
    if VetAccess.objects.filter(vet=request.user, pet=pet).exists():
        messages.info(request, 'У вас уже есть доступ к этому питомцу.')
        return redirect('vet_patient_search')

    # Уже есть активная заявка?
    existing = VetAccessRequest.objects.filter(
        vet=request.user, pet=pet, status='pending'
    ).first()
    if existing:
        existing.access_level = level
        existing.message = request.POST.get('message', '')
        existing.save(update_fields=['access_level', 'message'])
        messages.info(request, 'Заявка обновлена.')
    else:
        VetAccessRequest.objects.create(
            vet=request.user,
            pet=pet,
            access_level=level,
            message=request.POST.get('message', ''),
        )
        messages.success(request, 'Заявка отправлена. Ожидайте подтверждения владельца.')

    return redirect('vet_patient_search')


@login_required
def vet_requests_list(request):
    """Список заявок текущего ветеринара и выданных доступов."""
    if request.user.role != 'vet':
        return redirect('home')

    requests_qs = VetAccessRequest.objects.filter(vet=request.user).select_related('pet', 'pet__owner')
    accesses_qs = VetAccess.objects.filter(vet=request.user).select_related('pet', 'pet__owner')

    return render(request, 'vet/requests_list.html', {
        'requests': requests_qs,
        'accesses': accesses_qs,
    })


@login_required
def vet_access_respond(request, pk, action):
    """POST — владелец одобряет/отклоняет заявку ветеринара."""
    if request.method != 'POST':
        return redirect('home')

    req = get_object_or_404(VetAccessRequest, pk=pk)
    if req.pet.owner != request.user:
        messages.error(request, 'Недостаточно прав.')
        return redirect('home')

    if action == 'approve':
        req.status = VetAccessRequest.Status.APPROVED
        req.responded_at = timezone.now()
        req.save(update_fields=['status', 'responded_at'])

        VetAccess.objects.update_or_create(
            vet=req.vet, pet=req.pet,
            defaults={'access_level': req.access_level},
        )
        messages.success(request, f'Доступ для {req.vet.get_full_name() or req.vet.username} одобрен.')
    elif action == 'reject':
        req.status = VetAccessRequest.Status.REJECTED
        req.responded_at = timezone.now()
        req.save(update_fields=['status', 'responded_at'])
        messages.success(request, 'Заявка отклонена.')

    return redirect(reverse('home') + '#notifications')


@login_required
def reminder_update_status(request, pk):
    """POST — быстрое обновление статуса прошедшего напоминания из уведомлений."""
    if request.method != 'POST':
        return redirect('home')
    r = get_object_or_404(Reminder, pk=pk)
    if not r.pet.can_edit(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('home')

    new_status = request.POST.get('status', 'completed')
    if new_status in dict(Reminder.Status.choices):
        r.status = new_status
        r.save(update_fields=['status'])
        messages.success(request, 'Статус напоминания обновлён.')
    return redirect(reverse('home') + '#notifications')