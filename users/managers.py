from django.contrib.auth.models import BaseUserManager
from string import ascii_lowercase, ascii_uppercase, digits


class UserManager(BaseUserManager):
    def create_user(self, email, password):
        if password is None:
            password = self.make_random_password(length=12,
                                                 allowed_chars=ascii_lowercase + ascii_uppercase + digits)
        user = self.model()
        user.email = email
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password)
        user.is_admin = True
        user.save(using=self._db)
        return user