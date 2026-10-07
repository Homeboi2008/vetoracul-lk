from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse, NoReverseMatch
from django.utils.functional import SimpleLazyObject

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    """
    Позволяет входить по username или email.
    Запрещает вход администраторам (is_staff/is_superuser) через
    обычную форму логина — только через /admin/.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None

        try:
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.DoesNotExist:
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).order_by('id').first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            # ---- Блокировка админов вне /admin/ ----
            if (user.is_staff or user.is_superuser) and not self._is_admin_request(request):
                return None
            # ----------------------------------------
            return user
        return None

    @staticmethod
    def _is_admin_request(request):
        """True, если запрос идёт с /admin/ (или другого admin:index URL)."""
        if request is None:
            return False
        try:
            admin_prefix = reverse('admin:index')  # обычно '/admin/'
        except NoReverseMatch:
            return False
        return request.path.startswith(admin_prefix)