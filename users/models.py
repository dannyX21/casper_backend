from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from users.managers import UserManager

class User(AbstractBaseUser):
    first_name = models.CharField(max_length=64, null=False, blank=False)
    last_name = models.CharField(max_length=64, null=False, blank=False)
    email = models.EmailField(max_length=128, null=False, blank=False, unique=True)
    is_staff = models.BooleanField(null=False, blank=False, default=False)
    is_active = models.BooleanField(null=False, blank=False, default=False)
    is_admin = models.BooleanField(null=False, default=False, blank=True)
    is_superuser = models.BooleanField(null=False, blank=False, default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(max_length=32, null=True, default='127.0.0.1', blank=True)
    date_joined = models.DateTimeField(null=False, auto_now_add=True)

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'
    objects = UserManager()

    class Meta:
        db_table = 'users'
        managed = True

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_short_name(self):
        return self.first_name

    def __unicode__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

