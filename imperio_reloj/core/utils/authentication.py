from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None
        
        try:
            token = auth_header.split(" ")[1]
            decoded = AccessToken(token)

            return(decoded, None)
        
        except Exception:
            raise AuthenticationFailed("Token Inválido")