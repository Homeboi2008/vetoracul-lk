from datetime import timedelta

from django.views.generic import TemplateView, View, CreateView, FormView, ListView, UpdateView, DeleteView, DetailView
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView
from django.contrib.auth import login
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q

from .models import Subscription, EmailVerificationCode, User, Pet, Reminder, Folder, Document
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordResetForm, CustomSetPasswordForm, VerificationCodeForm, PetForm, FolderForm, DocumentUploadForm



class SubscriptionView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Страница управления подпиской.
    Доступна только обычным пользователям (не ветеринарам).
    """
    template_name = 'subscription/subscription.html'

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

    def form_invalid(self, form):
        messages.error(self.request, 'Неверное имя пользователя или пароль.')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    next_page = 'login'


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'auth/profile.html'

class VerifyEmailView(FormView):
    form_class = VerificationCodeForm
    template_name = 'auth/verify_email.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        # Проверяем, есть ли в сессии ID пользователя
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
        # Удаляем код, больше не нужен
        EmailVerificationCode.objects.filter(user=self.user).delete()
        # Автоматически логиним пользователя
        login(self.request, self.user)
        messages.success(self.request, 'Ваш email подтверждён! Добро пожаловать.')
        # Очищаем сессию
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
    success_url = reverse_lazy('folder_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['owner'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
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
    success_url = reverse_lazy('folder_list')

    def test_func(self):
        return self.get_object().owner == self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Папка удалена.')
        return super().form_valid(form)


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
        if not (
            request.user == self.pet.owner
            or request.user in self.pet.co_owners.all()
            or request.user.role == 'vet'
        ):
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
        # Проверка доступа
        if not (doc.pet.owner == request.user or request.user in doc.pet.co_owners.all()):
            messages.error(request, 'Нет доступа.')
            return redirect('trash')
        doc.restore()
        messages.success(request, 'Документ восстановлен.')
        return redirect('trash')


class DocumentPermanentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if not (doc.pet.owner == request.user or request.user in doc.pet.co_owners.all()):
            messages.error(request, 'Нет доступа.')
            return redirect('trash')
        # Удаляем файл с диска
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, 'Документ удалён безвозвратно.')
        return redirect('trash')


class DocumentSoftDeleteView(LoginRequiredMixin, View):
    """Обычное удаление — отправка в корзину."""
    def post(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if not (doc.pet.owner == request.user or request.user in doc.pet.co_owners.all()):
            messages.error(request, 'Нет доступа.')
            return redirect('folder_list')
        doc.soft_delete()
        messages.success(request, 'Документ перемещён в корзину.')
        return redirect('folder_list')


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
        pet = self.get_object()
        user = self.request.user
        return (
            user.role == 'vet'
            or pet.owner == user
            or user in pet.co_owners.all()
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pet = self.get_object()
        ctx['diagnoses'] = pet.diagnoses.order_by('-date')
        ctx['documents'] = pet.documents.filter(is_deleted=False).order_by('-date')
        ctx['reminders'] = pet.reminders.order_by('date', 'time')
        return ctx


class PetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Pet
    form_class = PetForm
    template_name = 'pets/pet_form.html'
    success_url = reverse_lazy('pet_list')

    def test_func(self):
        pet = self.get_object()
        return pet.owner == self.request.user or self.request.user in pet.co_owners.all()

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
        # Удалять может только владелец
        return self.get_object().owner == self.request.user

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
    """Проверяет, что пользователь имеет доступ к питомцу (владелец/совладелец/ветеринар)."""
    def get_pet(self):
        pet = get_object_or_404(Pet, pk=self.kwargs['pet_pk'])
        user = self.request.user
        if not (user.role == 'vet' or pet.owner == user or user in pet.co_owners.all()):
            messages.error(self.request, 'Нет доступа к этому питомцу.')
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.pet = self.pet
        messages.success(self.request, 'Диагноз добавлен.')
        return super().form_valid(form)

    def get_success_url(self):
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
        # Разрешаем редактировать только диагнозы своих питомцев или если ветеринар
        user = self.request.user
        if user.role == 'vet':
            return Diagnosis.objects.all()
        return Diagnosis.objects.filter(
            Q(pet__owner=user) | Q(pet__co_owners=user)
        ).distinct()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Диагноз обновлён.')
        return super().form_valid(form)

    def get_success_url(self):
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
            Q(pet__owner=user) | Q(pet__co_owners=user)
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

    def get_success_url(self):
        return reverse_lazy('pet_detail', kwargs={'pk': self.pet.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['pet'] = self.pet
        ctx['title'] = 'Загрузить документ'
        return ctx


class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'pets/document_form.html'

    def get_queryset(self):
        user = self.request.user
        if user.role == 'vet':
            return Document.objects.filter(is_deleted=False)
        return Document.objects.filter(is_deleted=False).filter(
            Q(pet__owner=user) | Q(pet__co_owners=user)
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
        return reverse_lazy('pet_detail', kwargs={'pk': self.pet.pk})

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
            return Reminder.objects.all()
        return Reminder.objects.filter(
            Q(pet__owner=user) | Q(pet__co_owners=user)
        ).distinct()

    def form_valid(self, form):
        messages.success(self.request, 'Напоминание обновлено.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('pet_detail', kwargs={'pk': self.object.pet.pk})

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
            return Reminder.objects.all()
        return Reminder.objects.filter(
            Q(pet__owner=user) | Q(pet__co_owners=user)
        ).distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['object_type'] = 'напоминание'
        ctx['cancel_url'] = reverse_lazy('pet_detail', kwargs={'pk': self.object.pet.pk})
        return ctx

    def get_success_url(self):
        return reverse_lazy('pet_detail', kwargs={'pk': self.object.pet.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Напоминание удалено.')
        return super().form_valid(form)