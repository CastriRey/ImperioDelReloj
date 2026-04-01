from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
import jwt
from django.conf import settings

SECRET_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc0OTk4MjUyLCJpYXQiOjE3NzQ5OTQ2NTIsImp0aSI6ImNhZjNkMWY3NzczZDQwYTE5MDY1YTU2MWUyYTM4MjNlIiwiZW1wbGVhZG9faWQiOjEwMjIxNDM5NTgsImNvcnJlbyI6ImRhdmlkY2FzdHJpbGxvbjA0QGdtYWlsLmNvbSIsInBlcmZpbCI6MX0.yx5d9ivT2y9NuKGBl5errOfnPPiewmsrwuMTzK91TYA"  # usa la misma del login


class CustomJWTAuthentication(BaseAuthentication):

    def authenticate(self, request):

        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        try:
            prefix, token = auth_header.split()

            if prefix != 'Bearer':
                raise AuthenticationFailed('Token inválido')

            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

            # 🔥 AQUÍ ESTÁ LA CLAVE
            user = type('User', (), {})()  # usuario falso
            user.payload = payload

            return (user, None)

        except Exception as e:
            raise AuthenticationFailed(f'Error en token: {str(e)}')