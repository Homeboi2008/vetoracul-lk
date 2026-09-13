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


from .views import (
    FolderListView, FolderCreateView, FolderUpdateView, FolderDeleteView, FolderDetailView,
    DocumentUploadView, TrashListView, DocumentRestoreView, DocumentPermanentDeleteView, DocumentSoftDeleteView,
)

urlpatterns += [
    # Папки
    path('cabinet/', FolderListView.as_view(), name='folder_list'),
    path('cabinet/folder/create/', FolderCreateView.as_view(), name='folder_create'),
    path('cabinet/folder/<int:pk>/', FolderDetailView.as_view(), name='folder_detail'),
    path('cabinet/folder/<int:pk>/edit/', FolderUpdateView.as_view(), name='folder_edit'),
    path('cabinet/folder/<int:pk>/delete/', FolderDeleteView.as_view(), name='folder_delete'),

    # Документы
    path('pet/<int:pet_pk>/document/upload/', DocumentUploadView.as_view(), name='document_upload'),
    path('document/<int:pk>/delete/', DocumentSoftDeleteView.as_view(), name='document_soft_delete'),

    # Корзина
    path('cabinet/trash/', TrashListView.as_view(), name='trash'),
    path('cabinet/trash/<int:pk>/restore/', DocumentRestoreView.as_view(), name='document_restore'),
    path('cabinet/trash/<int:pk>/delete/', DocumentPermanentDeleteView.as_view(), name='document_permanent_delete'),
]


from .views import (
    PetListView, PetCreateView, PetDetailView, PetUpdateView, PetDeleteView,
)

urlpatterns += [
    path('pets/', PetListView.as_view(), name='pet_list'),
    path('pets/add/', PetCreateView.as_view(), name='pet_add'),
    path('pets/<int:pk>/', PetDetailView.as_view(), name='pet_detail'),
    path('pets/<int:pk>/edit/', PetUpdateView.as_view(), name='pet_edit'),
    path('pets/<int:pk>/delete/', PetDeleteView.as_view(), name='pet_delete'),
]

from .views import (
    DiagnosisCreateView, DiagnosisUpdateView, DiagnosisDeleteView,
    DocumentCreateView, DocumentUpdateView,
    ReminderCreateView, ReminderUpdateView, ReminderDeleteView,
)

urlpatterns += [
    # Диагнозы
    path('pets/<int:pet_pk>/diagnosis/add/', DiagnosisCreateView.as_view(), name='diagnosis_add'),
    path('diagnosis/<int:pk>/edit/', DiagnosisUpdateView.as_view(), name='diagnosis_edit'),
    path('diagnosis/<int:pk>/delete/', DiagnosisDeleteView.as_view(), name='diagnosis_delete'),

    # Документы
    path('pets/<int:pet_pk>/document/add/', DocumentCreateView.as_view(), name='document_add'),
    path('document/<int:pk>/edit/', DocumentUpdateView.as_view(), name='document_edit'),

    # Напоминания
    path('pets/<int:pet_pk>/reminder/add/', ReminderCreateView.as_view(), name='reminder_add'),
    path('reminder/<int:pk>/edit/', ReminderUpdateView.as_view(), name='reminder_edit'),
    path('reminder/<int:pk>/delete/', ReminderDeleteView.as_view(), name='reminder_delete'),
]