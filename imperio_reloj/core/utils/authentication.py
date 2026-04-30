from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings


class CustomJWTAuthentication(BaseAuthentication):

    def authenticate(self, request):

        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split()

            if prefix != 'Bearer':
                raise AuthenticationFailed('Token inválido')

            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

            user = type('User', (), {})()
            user.payload = payload

            return (user, None)

        except Exception as e:
            raise AuthenticationFailed(f'Error en token: {str(e)}')