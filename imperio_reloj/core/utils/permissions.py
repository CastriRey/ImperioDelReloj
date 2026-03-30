from rest_framework.response import Response
from rest_framework import status
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