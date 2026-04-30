from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission
from core.models import Permiso, Ruta
from django.db import connection


def _match_route_pattern(path, route_pattern):
    """Match a request path against a ruta pattern with dynamic segments."""
    path_segments = path.strip('/').split('/')
    pattern_segments = route_pattern.strip('/').split('/')

    if len(path_segments) != len(pattern_segments):
        return False

    for path_seg, pattern_seg in zip(path_segments, pattern_segments):
        if pattern_seg.startswith('<') and pattern_seg.endswith('>'):
            if pattern_seg.startswith('<int:') and not path_seg.isdigit():
                return False
            continue
        if pattern_seg.startswith('{') and pattern_seg.endswith('}'):
            continue
        if pattern_seg != path_seg:
            return False

    return True


def _find_route_for_path(path):
    ruta = Ruta.objects.filter(url_ruta__iexact=path).first()
    if ruta:
        return ruta

    rutas = Ruta.objects.all()
    for ruta in rutas:
        if _match_route_pattern(path, ruta.url_ruta):
            return ruta

    return None


class PermisoDinamico(BasePermission):

    def has_permission(self, request, view):
        try:
            user = request.user
            payload = getattr(user, 'payload', None)

            if not payload:
                return False

            perfil = payload.get('perfil')

            # El perfil supremo (por ejemplo 1) tiene acceso total.
            if perfil == 1 or perfil == '1':
                return True

            if not perfil:
                return False

            path = request.path
            metodo = request.method

            ruta = _find_route_for_path(path)

            if not ruta:
                return False

            permiso = Permiso.objects.filter(
                codigo_perfil_permiso=int(perfil),
                codigo_ruta_permiso=int(ruta.codigo_ruta)
            ).first()

            if not permiso:
                return False

            if metodo == 'GET' and permiso.consultar.strip().upper() == 'S':
                return True
            elif metodo == 'POST' and permiso.insertar.strip().upper() == 'S':
                return True
            elif metodo in ['PUT', 'PATCH'] and permiso.modificar.strip().upper() == 'S':
                return True
            elif metodo == 'DELETE' and permiso.eliminar.strip().upper() == 'S':
                return True

            return False

        except Exception:
            return False