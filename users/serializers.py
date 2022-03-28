from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from users.utils import password_check
from users.models import User

class UserSerializer(serializers.ModelSerializer):
    pending_requests = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = (
          'id',
          'email',
          'first_name',
          'last_name',
          'is_active',
          'is_staff',
          'is_admin',
          'is_superuser',
          'date_joined',
          'pending_requests',
        )
        read_only_fields = ('date_joined', 'is_active', 'is_staff', 'is_admin',)
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def to_internal_value(self, data):
        internal_value = super(UserSerializer, self).to_internal_value(data)
        if data.get('password') is not None:
            internal_value['password'] = data['password']

        if data.get('new_password') is not None:
            internal_value['new_password'] = data['new_password']

        return internal_value

    def validate(self, data):
        password = data.pop('password', None)
        new_password = data.pop('new_password', None)
        validated_data = super(UserSerializer, self).validate(data)
        if self.instance is None:
            if password is not None:
                password_validation = password_check(password)
                if not password_validation.get('password_ok', False):
                    raise serializers.ValidationError(', '.join((f'{key}: {"true" if value else "false"}' for(key, value) in password_validation.items())))

                validated_data['password'] = password

            else:
                raise ValidationError('Password is required!')

        elif new_password is not None:
            if password is None:
                raise serializers.ValidationError('Must provide current password!')

            if not self.instance.check_password(password):
                raise serializers.ValidationError('Wrong password!')

            password_validation = password_check(new_password)
            if not password_validation.get('password_ok', False):
                raise serializers.ValidationError(', '.join((f'{key}: {"true" if value else "false"}' for(key, value) in password_validation.items())))

            validated_data['password'] = new_password

        if not data.get('email').lower().strip().endswith('belf.com'):
            raise serializers.ValidationError('Only email addresses from "belf.com" domain are allowed!')

        return validated_data

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password is not None:
            user.set_password(password)
            user.save()

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password is not None:
            instance.set_password(password)

        return super(UserSerializer, self).update(instance, validated_data)

    def get_pending_requests(self, instance):
        if instance.is_admin:
            requests = User.objects.filter(is_active=False, is_admin=False)
            serializer = UserSerializer(requests[:5], many=True, context=self.context)
            return serializer.data

        return None
