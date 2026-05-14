from .models import Empleado
import jwt
from django.conf import settings


def user_context(request):
    """
    Context processor que añade información del usuario autenticado al contexto de templates.
    Obtiene el usuario desde el JWT token almacenado en localStorage (vía cookies o headers).
    """
    user_info = {
        'current_user': None,
        'user_name': None,
        'user_full_name': None,
    }

    # Intentar obtener el token desde diferentes fuentes
    token = None

    # 1. Desde headers (para APIs)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]

    # 2. Desde cookies (si se almacena ahí)
    if not token:
        token = request.COOKIES.get('access_token')

    # 3. Desde la sesión (si existe)
    if not token and hasattr(request, 'session'):
        token = request.session.get('access_token')

    if token:
        try:
            # Decodificar el JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

            # Intentar diferentes claves para el user_id
            user_id = None

            # Posibles claves en el payload
            possible_keys = ['user_id', 'user', 'id', 'identificacion_empleado', 'empleado_id']
            for key in possible_keys:
                if key in payload:
                    user_id = payload[key]
                    break

            # Si no encontramos con las claves estándar, intentar con el payload completo
            if not user_id and 'user' in payload:
                user_obj = payload['user']
                if isinstance(user_obj, dict) and 'id' in user_obj:
                    user_id = user_obj['id']

            if user_id:
                # Buscar el empleado en la base de datos
                try:
                    empleado = Empleado.objects.get(identificacion_empleado=user_id)
                    user_info['current_user'] = empleado
                    user_info['user_name'] = f"{empleado.nombre_empleado} {empleado.primer_apellido_empleado}"
                    user_info['user_full_name'] = f"{empleado.nombre_empleado} {empleado.primer_apellido_empleado} {empleado.segundo_apellido_empleado or ''}".strip()
                except Empleado.DoesNotExist:
                    pass

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError, Exception) as e:
            # Token inválido o expirado, continuar sin usuario
            pass

    return user_info