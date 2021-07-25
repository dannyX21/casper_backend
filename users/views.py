from django_filters.rest_framework import DjangoFilterBackend
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework import filters
from rest_framework.decorators import action
from rest_framework.response import Response
from users.models import User
from users.serializers import UserSerializer
from users.permissions import UserPermission

class UserView(mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet):

    serializer_class = UserSerializer
    permission_classes = (AllowAny, UserPermission,)
    pagination_class = PageNumberPagination
    queryset = User.objects.all().order_by('id')

    def get_queryset(self):
        queryset = self.queryset
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(date_joined__isnull=True)

        elif not self.request.user.is_admin:
            queryset = queryset.filter(id=self.request.user.id)

        return queryset

    @action(detail=False, methods=['post',], url_path='check-email', permission_classes=(AllowAny,))
    def check_email(self, request):
        if 'email' not in request.data:
            return Response({'error': 'email is required!'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            email = request.data['email']
            validate_email(email)
            return Response({
                'email': email,
                'exists': User.objects.filter(email=email).exists()
            }, status=status.HTTP_200_OK)

        except ValidationError:
            return Response({'email': f'Email \'{email}\' is not valid!'}, status=status.HTTP_400_BAD_REQUEST)
