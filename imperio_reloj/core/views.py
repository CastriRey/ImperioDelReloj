from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Cliente, Empleado
from .serializers import ClienteSerializer, EmpleadoSerializer
from django.contrib.auth.hashers import check_password, make_password


# Create your views here.

'''
# Que hacen los ModelViewSet?
Los ModelViewSet nos crea automaticamente los metodos
get, post, put, delete para no tener que escribir codigo extra
'''

class EmpleadoViewset(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

@api_view(['GET'])
def listar_clientes(request):
    clientes = Cliente.objects.all()
    serializer = ClienteSerializer(clientes, many=True)
    return Response(serializer.data)

# Login del Empleado
@api_view(['POST'])
def login_empleado(request):
    correo = request.data.get('correo')
    contrasena = request.data.get('contrasena')

    try:
        empleado = Empleado.objects.get(correo_empleado = correo)

        # Validar Contraseña
        if check_password(contrasena, empleado.hash_contrasena_empleado):
            return Response({
                "mensaje": "Login Exitoso",
                "empleado": {
                    "id": empleado.identificacion_empleado,
                    "nombre": empleado.nombre_empleado,
                    "correo": empleado.correo_empleado
                }
            })
        else:
            return Response(
            {
                "error": "Contraseña incorrecta"
            }, status = 401)
        
    except Empleado.DoesNotExist:
        return Response({"error": "Empleado no encontrado"}, status = 404)

@api_view(['POST'])
def crear_empleado(request):
    try:

        #Validar Campos Obligatorios
        campos_obligatorios = [
            'identificacion',
            'nombre',
            'primer_apellido',
            'correo',
            'telefono',
            'direccion',
            'contrasena',
            'codigo_perfil'
        ]

        #Verificar cada campo
        for campo in campos_obligatorios:
            if not request.data.get(campo):
                return Response(
                    {
                        "error": f"El campo {campo} es obligatorio"
                    }, status=400
                )
            
        if Empleado.objects.filter(correo_empleado=request.data.get('correo')).exists():
            return Response({"error": "El correo ya existe"}, status=400)
            

        empleado = Empleado(
            identificacion_empleado = request.data.get('identificacion'),
            nombre_empleado = request.data.get('nombre'),
            primer_apellido_empleado = request.data.get('primer_apellido'),
            segundo_apellido_empleado = request.data.get('segundo_apellido'),
            correo_empleado = request.data.get('correo'),
            telefono_empleado = request.data.get('telefono'),
            direccion_empleado = request.data.get('direccion'),
            hash_contrasena_empleado = make_password(request.data.get('contrasena')),
            codigo_perfil_empleado = request.data.get('codigo_perfil')
        )

        empleado.save()

        return Response({"mensaje": "Empleado creado correctamente"})
    
    except Exception as e:
        return Response({"error": str(e)}, status=400)