from django.urls import path
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetCompleteView
from django.views.generic import TemplateView

from .views import (
    RegisterView, CustomLoginView, CustomLogoutView,
    CustomPasswordResetView, CustomPasswordResetConfirmView,
    ProfileView, SubscriptionView, CreateSubscriptionView,
    VerifyEmailView, ResendCodeView
)



urlpatterns = [
    path('subscription/', SubscriptionView.as_view(), name='subscription'),
    path('subscription/create/', CreateSubscriptionView.as_view(), name='create_subscription'),
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-code/', ResendCodeView.as_view(), name='resend_code'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('', TemplateView.as_view(template_name='auth/home.html'), name='home'),
]