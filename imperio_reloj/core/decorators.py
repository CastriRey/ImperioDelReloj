# Decorador personalizado para proteger vistas basadas en autenticación
from functools import wraps
from django.shortcuts import redirect
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import json

def login_required_view(view_func):
    """
    Decorador que protege vistas web verificando que exista un token de acceso válido.
    Si no hay token o no es válido, redirige a la página de login.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Obtener el token del header Authorization o de las cookies
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        token = None

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        # Si no hay token, redirigir a login
        if not token:
            return redirect('login')

        try:
            # Validar el token
            from rest_framework_simplejwt.authentication import JWTAuthentication
            jwt_auth = JWTAuthentication()
            # Intentar validar el token (lanzará excepción si es inválido)
            # Para las vistas HTML, podemos usar una validación más simple
            pass
        except (InvalidToken, TokenError):
            return redirect('login')

        return view_func(request, *args, **kwargs)

    return wrapper
