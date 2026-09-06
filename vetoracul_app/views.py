from datetime import timedelta

from django.views.generic import TemplateView, View, CreateView, FormView
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView
from django.contrib.auth import login
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse_lazy
from django.utils import timezone

from .models import Subscription, EmailVerificationCode, User
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordResetForm, CustomSetPasswordForm, VerificationCodeForm



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