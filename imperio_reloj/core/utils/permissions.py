from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission
from core.models import Permiso, Ruta
from django.db import connection

# def has_permission(self, request, view):
#         try:
#             perfil = request.user.get('perfil')
#             path = request.path
#             metodo = request.method

#             ruta = Ruta.objects.get(url_ruta=path)

#             permiso = Permiso.objects.get(
#                 codigo_perfil_permiso=perfil,
#                 codigo_ruta_permiso=ruta.codigo_ruta
#             )

#             if metodo == 'GET' and permiso.consultar.strip().upper() != 'S':
#                 return False

#             if metodo == 'POST' and permiso.insertar.strip().upper() != 'S':
#                 return False

#             if metodo in ['PUT', 'PATCH'] and permiso.modificar.strip().upper() != 'S':
#                 return False

#             if metodo == 'DELETE' and permiso.eliminar.strip().upper() != 'S':
#                 return False

#             return True

        # except Exception as e:
        #     print("ERROR PERMISOS:", str(e))
        #     return False

class PermisoDinamico(BasePermission):

    def has_permission(self, request, view):

        try:
            print("\n==== DEBUG PERMISOS ====")

            # 🔐 TOKEN
            print("Header: ", request.headers.get('Authorization'))

            user = request.user
            payload = getattr(user, 'payload', None)

            print("PAYLOAD:", payload)

            if not payload:
                print("❌ No hay payload")
                return False

            perfil = payload.get('perfil')
            print("perfil:", perfil)

            # 🌐 REQUEST
            path = request.path
            metodo = request.method

            print("path:", path)
            print("metodo:", metodo)
            print("PATH RAW:", repr(path))
            print("PATH LEN:", len(path))

            # 🔍 DEBUG RUTAS
            print("\n==== RUTAS EN BD ====")
            rutas = Ruta.objects.all()

            for r in rutas:
                print(f"BD: {repr(r.url_ruta)} == PATH: {repr(path)} -> {r.url_ruta == path}")

            # 🔎 BUSCAR RUTA
            ruta = Ruta.objects.filter(url_ruta__iexact=path).first()

            if not ruta:
                print("❌ Ruta no encontrada:", path)
                return False

            print("✅ Ruta encontrada:", ruta.codigo_ruta)

            # 🧪 DEBUG TIPOS
            print(type(ruta.codigo_ruta), ruta.codigo_ruta)
            print(type(perfil), perfil)

            # 🔎 BUSCAR PERMISO (ORM)
            permiso = Permiso.objects.filter(
                codigo_perfil_permiso=int(perfil),
                codigo_ruta_permiso=int(ruta.codigo_ruta)
            ).first()

            print("\n==== RESULTADO ORM ====")
            print("permiso:", permiso)

            # 🔎 DEBUG DIRECTO A ORACLE (CURSOR)
            print("\n==== PERMISOS DESDE ORACLE (CURSOR) ====")

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT CODIGO_PERFIL_PERMISO, CODIGO_RUTA_PERMISO, CONSULTAR
                    FROM PERMISOS
                """)
                rows = cursor.fetchall()

                for row in rows:
                    print(row)

            # 🔎 DEBUG CONEXIÓN
            print("\n==== CONEXIÓN DJANGO ====")
            print("USER:", connection.settings_dict['USER'])
            print("NAME:", connection.settings_dict['NAME'])

            # 🚫 SI NO EXISTE PERMISO
            if not permiso:
                print("❌ Permiso no encontrado en ORM")
                return False

            # ✅ VALIDAR SEGÚN MÉTODO
            if metodo == 'GET':
                if permiso.consultar == 'S':
                    print("✅ Permiso de CONSULTAR concedido")
                    return True
                else:
                    print("❌ No tiene permiso de CONSULTAR")
                    return False

            elif metodo == 'POST':
                return permiso.insertar == 'S'

            elif metodo in ['PUT', 'PATCH']:
                return permiso.modificar == 'S'

            elif metodo == 'DELETE':
                return permiso.eliminar == 'S'

            # ❌ Método no contemplado
            return False

        except Exception as e:
            print("💥 ERROR PERMISOS:", str(e))
            return False