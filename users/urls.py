from django.urls import path, include
from rest_framework import routers
from users.views import UserView

router = routers.SimpleRouter()
router.register(r'users', UserView)

urlpatterns = [
  path('', include(router.urls)),
]