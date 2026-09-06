from datetime import timedelta

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .models import User, Pet, Diagnosis, Document, Reminder, Subscription


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Админка для кастомной модели User.
    Расширяет стандартный UserAdmin, добавляя наши поля.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'phone', 'city', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'city')}),
        (_('Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'phone', 'city'),
        }),
    )


class DiagnosisInline(admin.TabularInline):
    model = Diagnosis
    extra = 1
    fields = ('diagnosis_text', 'date', 'vet', 'status')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('vet',)
    show_change_link = True


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1
    fields = ('title', 'file', 'date', 'uploaded_by')
    readonly_fields = ('uploaded_at',)
    autocomplete_fields = ('uploaded_by',)
    show_change_link = True


class ReminderInline(admin.TabularInline):
    model = Reminder
    extra = 1
    fields = ('title', 'reminder_type', 'date', 'time', 'status', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('created_by',)
    show_change_link = True


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'animal_type', 'owner', 'gender', 'birth_date', 'weight', 'created_at')
    list_filter = ('animal_type', 'gender', 'owner')
    search_fields = ('name', 'owner__first_name', 'owner__last_name', 'owner__username')
    autocomplete_fields = ('owner', 'co_owners')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('owner', 'co_owners', 'name', 'animal_type', 'gender', 'birth_date', 'weight')}),
        ('Системные', {'fields': ('created_at', 'updated_at')}),
    )
    inlines = (DiagnosisInline, DocumentInline, ReminderInline)
    ordering = ('-created_at',)


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('pet', 'diagnosis_text_short', 'date', 'vet', 'status', 'created_at')
    list_filter = ('status', 'date', 'vet')
    search_fields = ('pet__name', 'diagnosis_text', 'vet__first_name', 'vet__last_name')
    autocomplete_fields = ('pet', 'vet')
    readonly_fields = ('created_at',)
    ordering = ('-date',)

    def diagnosis_text_short(self, obj):
        return obj.diagnosis_text[:50] + '…' if len(obj.diagnosis_text) > 50 else obj.diagnosis_text
    diagnosis_text_short.short_description = 'Диагноз (сокращённо)'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'pet', 'date', 'uploaded_by', 'uploaded_at')
    list_filter = ('date', 'uploaded_by')
    search_fields = ('title', 'pet__name', 'uploaded_by__first_name', 'uploaded_by__last_name')
    autocomplete_fields = ('pet', 'uploaded_by')
    readonly_fields = ('uploaded_at',)
    ordering = ('-date',)


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'pet', 'reminder_type', 'date', 'time', 'status', 'created_by', 'is_past')
    list_filter = ('reminder_type', 'status', 'date', 'created_by')
    search_fields = ('title', 'pet__name', 'description')
    autocomplete_fields = ('pet', 'created_by')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('date', 'time')
    actions = ['mark_completed', 'mark_missed', 'mark_cancelled']

    def is_past(self, obj):
        return obj.is_past
    is_past.boolean = True
    is_past.short_description = 'Просрочено'

    @admin.action(description='Отметить выбранные как выполненные')
    def mark_completed(self, request, queryset):
        queryset.update(status=Reminder.Status.COMPLETED)

    @admin.action(description='Отметить выбранные как пропущенные')
    def mark_missed(self, request, queryset):
        queryset.update(status=Reminder.Status.MISSED)

    @admin.action(description='Отметить выбранные как отменённые')
    def mark_cancelled(self, request, queryset):
        queryset.update(status=Reminder.Status.CANCELLED)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'end_date', 'is_active', 'status', 'payment_amount', 'payment_method', 'created_at')
    list_filter = ('status', 'is_active', 'payment_method', 'start_date', 'end_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'payment_id')
    autocomplete_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-start_date',)
    actions = ['activate_selected', 'deactivate_selected']

    @admin.action(description='Активировать выбранные подписки')
    def activate_selected(self, request, queryset):
        # При активации проверяем, чтобы дата окончания была не в прошлом
        for sub in queryset:
            sub.is_active = True
            sub.status = Subscription.Status.ACTIVE
            if sub.end_date < timezone.now().date():
                sub.end_date = timezone.now().date() + timedelta(days=30)
            sub.save()
        self.message_user(request, f'Активировано {queryset.count()} подписок.')

    @admin.action(description='Деактивировать выбранные подписки')
    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False, status=Subscription.Status.CANCELLED)
        self.message_user(request, f'Деактивировано {queryset.count()} подписок.')