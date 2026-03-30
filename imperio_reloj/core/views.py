from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated 
from .models import Cliente, Empleado
from .serializers import ClienteSerializer, EmpleadoSerializer
from django.contrib.auth.hashers import check_password, make_password
from django.db import connection
from .utils.permissions import validar_permiso
from .utils.authentication import CustomJWTAuthentication

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

# @api_view(['GET'])
# def listar_clientes(request):
#     clientes = Cliente.objects.all()
#     serializer = ClienteSerializer(clientes, many=True)
#     return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_clientes(request):
    clientes = Cliente.objects.all().values()
    return Response(clientes)

# Login del Empleado
@api_view(['POST'])
def login_empleado(request):
    correo = request.data.get('correo')
    contrasena = request.data.get('contrasena')

    if not correo or not contrasena:
        return Response(
            {
                "error": "Correo y contraseña son obligatorios"
            }, status= 400
        )

    try:
        empleado = Empleado.objects.get(correo_empleado = correo)

        if not check_password(contrasena, empleado.hash_contrasena_empleado):
            return Response(
                {
                    "error:": "Credenciales invalidas"
                }, status= 401
            )
        
        # Generar Token Manual
        refresh = RefreshToken()

        refresh['empleado_id'] = empleado.identificacion_empleado
        refresh['correo'] = empleado.correo_empleado
        refresh['perfil'] = empleado.codigo_perfil_empleado

        # Validar Contraseña
        return Response({
            "mensaje": "Login Exitoso",
            "empleado": {
                "id": empleado.identificacion_empleado,
                "nombre": empleado.nombre_empleado,
                "correo": empleado.correo_empleado,
                "perfil": empleado.codigo_perfil_empleado
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })

    except Empleado.DoesNotExist:
        return Response(
            {
                "error": "Empleado no encontrado"
            }, status = 404
        )

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
    
@api_view(['POST'])
@authentication_classes([CustomJWTAuthentication])
def crear_cliente(request): 

    if not validar_permiso(request, 'POST'):
        return Response(
            {
                "error": "No tienes permiso para realizar esta acción"
            }, status = 403
        )
    
    print("Ya pasé por aquí")

    try:
        campos_obligatorios = [
            'identificacion',
            'nombre',
            'primer_apellido',
            'empleado'
        ]

        for campo in campos_obligatorios:
            if not request.data.get(campo):
                return Response(
                    {
                        "error": f"El campo {campo} es obligatorio"
                    }
                )
        
        # Validar que el empleado si exista
        if not Empleado.objects.filter(
            identificacion_empleado=request.data.get('empleado')
        ).exists():
            return Response(
                {
                    "error": "El empleado no existe"
                }, status=400
            )
        
        cliente = Cliente(
            identificacion_cliente = request.data.get('identificacion'),
            nombre_cliente = request.data.get('nombre'),
            primer_apellido_cliente = request.data.get('primer_apellido'),
            segundo_apellido_cliente = request.data.get('segundo_apellido'),
            correo_cliente = request.data.get('correo'),
            telefono_cliente = request.data.get('telefono'),
            identificacion_empleado = request.data.get('empleado'),
            comentarios = request.data.get('comentarios')
        )

        cliente.save()

        # Mostrar la última consulta ejecutada
        print(connection.queries[-1])

        return Response(
            {
                "mensaje": "Cliente creado correctamente"
            }
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e),
                "mensaje": "Ya pasé por aquí"
            }, status=400
        )