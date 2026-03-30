from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission
from core.models import Permiso, Ruta

def validar_permiso(request, accion):
    print('Validar Permiso')
    try:
        print("entré")
        # Se obtinen los datos del token
        empleado_id = request.user
        perfil = request.user.get('perfil')
        print(f"empleado_id: {empleado_id}")
        print(f"Perfil: {perfil}")


        # Se busca la ruta
        ruta = Ruta.objects.get(url_ruta = request.path)
        print("PATH: ", request.path)
        print(f"ruta: {ruta}")

        permiso = Permiso.objects.get(
            codigo_perfil_permiso = perfil,
            codigo_ruta_permiso = ruta.codigo_ruta
        )

        print(f"accion: {accion}")

        if accion == 'POST' and permiso.insertar != 'S':
            return False
        
        if accion in ['PUT', 'PATCH'] and permiso.modificar != 'S':
            return False
        
        if accion == 'DELETE' and permiso.eliminar != 'S':
            return False
        
        print('Validar Permiso')
        return True
    
    except Exception as e:
        print("ERROR REAL:", str(e))
        return False

class PermisoDinamico(BasePermission):
    def has_permision(self, request, view):
        try:
            perfil = request.user.get('perfil')
            path = request.path
            metodo = request.method

            ruta = ruta.objects.get(url_ruta=path)

            permiso = Permiso.objects.get(
                codigo_perfil_permiso=perfil,
                codigo_ruta_permiso=ruta.codigo_ruta
            )

            if metodo == 'POST' and permiso.insertar.strip().upper() != 'S':
                return False

            if metodo in ['PUT', 'PATCH'] and permiso.modificar.strip().upper() != 'S':
                return False

            if metodo == 'DELETE' and permiso.eliminar.strip().upper() != 'S':
                return False

            return True

        except Exception as e:
            print("ERROR PERMISOS:", str(e))
            return False
