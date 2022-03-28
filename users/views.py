from django_filters.rest_framework import DjangoFilterBackend
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
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

    def get_serializer_context(self):
        context = super(UserView, self).get_serializer_context()
        context['user'] = self.request.user
        return context

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

    @action(detail=False, methods=['get',], url_path='me', permission_classes=(IsAuthenticated,))
    def me(self, request):
        context = self.get_serializer_context()
        if 'user' in context:
            serializer = UserSerializer(context['user'], many=False, context=context)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({'error': 'User not found!'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['put',], url_path='approve', permission_classes=(IsAuthenticated,))
    def approve(self, request):
        context = self.get_serializer_context()
        if not context['user'].is_admin:
            return Response({'error': 'Only Admin users can activate accounts!'}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.data.get('id')
        if user_id is None:
            return Response({'error': 'User id is required!'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=int(user_id))

        except (User.DoesNotExist, ValueError):
            return Response({'error': f'User not found!'}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_active:
            return Response({'error': f'User with id: {user_id} has an active account!'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put',], url_path='reject', permission_classes=(IsAuthenticated,))
    def reject(self, request):
        context = self.get_serializer_context()
        if not context['user'].is_admin:
            return Response({'error': 'Only Admin users can reject accounts!'}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.data.get('id')
        if user_id is None:
            return Response({'error': 'User id is required!'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=int(user_id))

        except (User.DoesNotExist, ValueError):
            return Response({'error': f'User not found!'}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_active:
            return Response({'error': f'User with id: {user_id} has an active account!'}, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
