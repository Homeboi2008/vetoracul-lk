from django.urls import path
from django.contrib.auth.views import (
    PasswordResetDoneView, PasswordResetCompleteView
)
from . import views

urlpatterns = [
    # Главная
    path('', views.HomeView.as_view(), name='home'),

    # Аутентификация
    path('register/', views.RegisterView.as_view(), name='register'),
    path('register/vet/', views.VetRegisterView.as_view(), name='register_vet'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-code/', views.ResendCodeView.as_view(), name='resend_code'),
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # Сброс пароля
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password-reset/complete/', PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'), name='password_reset_complete'),

    # Питомцы
    path('pets/', views.PetListView.as_view(), name='pet_list'),
    path('pets/add/', views.PetCreateView.as_view(), name='pet_add'),
    path('pets/<int:pk>/', views.PetDetailView.as_view(), name='pet_detail'),
    path('pets/<int:pk>/edit/', views.PetUpdateView.as_view(), name='pet_edit'),
    path('pets/<int:pk>/delete/', views.PetDeleteView.as_view(), name='pet_delete'),

    # Диагнозы
    path('pets/<int:pet_pk>/diagnosis/add/', views.DiagnosisCreateView.as_view(), name='diagnosis_add'),
    path('diagnosis/<int:pk>/edit/', views.DiagnosisUpdateView.as_view(), name='diagnosis_edit'),
    path('diagnosis/<int:pk>/delete/', views.DiagnosisDeleteView.as_view(), name='diagnosis_delete'),

    # Документы
    path('pets/<int:pet_pk>/document/add/', views.DocumentCreateView.as_view(), name='document_add'),
    path('document/<int:pk>/edit/', views.DocumentUpdateView.as_view(), name='document_edit'),

    # Напоминания
    path('pets/<int:pet_pk>/reminder/add/', views.ReminderCreateView.as_view(), name='reminder_add'),
    path('reminder/<int:pk>/edit/', views.ReminderUpdateView.as_view(), name='reminder_edit'),
    path('reminder/<int:pk>/delete/', views.ReminderDeleteView.as_view(), name='reminder_delete'),

    # Кабинет / Папки
    path('cabinet/', views.FolderListView.as_view(), name='folder_list'),
    path('cabinet/folder/create/', views.FolderCreateView.as_view(), name='folder_create'),
    path('cabinet/folder/<int:pk>/', views.FolderDetailView.as_view(), name='folder_detail'),
    path('cabinet/folder/<int:pk>/edit/', views.FolderUpdateView.as_view(), name='folder_edit'),
    path('cabinet/folder/<int:pk>/delete/', views.FolderDeleteView.as_view(), name='folder_delete'),
    path('cabinet/trash/', views.TrashListView.as_view(), name='trash'),
    path('cabinet/trash/<int:pk>/restore/', views.DocumentRestoreView.as_view(), name='document_restore'),
    path('cabinet/trash/<int:pk>/delete/', views.DocumentPermanentDeleteView.as_view(), name='document_permanent_delete'),
    path('document/<int:pk>/delete/', views.DocumentSoftDeleteView.as_view(), name='document_soft_delete'),

    # Подписка
    path('subscription/', views.SubscriptionView.as_view(), name='subscription'),
    path('subscription/create/', views.CreateSubscriptionView.as_view(), name='create_subscription'),

    # Ветеринар
    path('vet/', views.VetDashboardView.as_view(), name='vet_dashboard'),
    path('vet/patient/<int:pk>/', views.VetPatientCardView.as_view(), name='vet_patient_card'),
    path('vet/patient/<int:pet_pk>/record/add/', views.VetMedicalRecordCreateView.as_view(), name='vet_medical_record_add'),
]