from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated 
from .models import *
from .serializers import ClienteSerializer, EmpleadoSerializer
from django.contrib.auth.hashers import check_password, make_password
from django.db import connection
from .utils.permissions import PermisoDinamico
from .utils.authentication import CustomJWTAuthentication
from datetime import date

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


def obtener_siguiente_valor(secuencia):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {secuencia}.NEXTVAL FROM DUAL")
        row = cursor.fetchone()
    return row[0]

# @api_view(['GET'])

# def listar_clientes(request):
#     clientes = Cliente.objects.all()
#     serializer = ClienteSerializer(clientes, many=True)
#     return Response(serializer.data)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def listar_clientes(request):
#     clientes = Cliente.objects.all().values()
#     return Response(clientes)


# Login del Empleado
@api_view(['POST'])
def login_empleado(request):
    return Response(
        {
            "mensaje": "Login desactivado temporalmente"
        }
    )
    # correo = request.data.get('correo')
    # contrasena = request.data.get('contrasena')

    # if not correo or not contrasena:
    #     return Response(
    #         {
    #             "error": "Correo y contraseña son obligatorios"
    #         }, status= 400
    #     )

    # try:
    #     empleado = Empleado.objects.get(correo_empleado = correo)

    #     if not check_password(contrasena, empleado.hash_contrasena_empleado):
    #         return Response(
    #             {
    #                 "error:": "Credenciales invalidas"
    #             }, status= 401
    #         )
        
    #     # Generar Token Manual
    #     refresh = RefreshToken()

        

    #     refresh['empleado_id'] = empleado.identificacion_empleado
    #     refresh['correo'] = empleado.correo_empleado
    #     refresh['perfil'] = empleado.codigo_perfil_empleado

    #     # Validar Contraseña
    #     return Response({
    #         "mensaje": "Login Exitoso",
    #         "empleado": {
    #             "id": empleado.identificacion_empleado,
    #             "nombre": empleado.nombre_empleado,
    #             "correo": empleado.correo_empleado,
    #             "perfil": empleado.codigo_perfil_empleado
    #         },
    #         "access": str(refresh.access_token),
    #         "refresh": str(refresh)
    #     })

    # except Empleado.DoesNotExist:
    #     return Response(
    #         {
    #             "error": "Empleado no encontrado"
    #         }, status = 404
    #     )

@api_view(['GET'])
def listar_clientes(request):

    try:
        print('USER:', request.user)
        print('HEADER:', request.headers.get('Authorization'))

        # 🔎 Parámetros de filtro
        nombre = request.query_params.get('nombre')
        correo = request.query_params.get('correo')

        # 📦 Query base (TODOS los clientes)
        clientes = Cliente.objects.all()

        # 🔍 FILTROS DINÁMICOS
        if nombre:
            clientes = clientes.filter(nombre_cliente__icontains=nombre)

        if correo:
            clientes = clientes.filter(correo_cliente__icontains=correo)

        # 🔽 ORDENAMIENTO
        clientes = clientes.order_by('-identificacion_cliente')

        # 📊 SERIALIZACIÓN MANUAL
        data = []

        for cliente in clientes:
            data.append({
                "identificacion": cliente.identificacion_cliente,
                "nombre": cliente.nombre_cliente,
                "primer_apellido": cliente.primer_apellido_cliente,
                "segundo_apellido": cliente.segundo_apellido_cliente,
                "correo": cliente.correo_cliente,
                "telefono": cliente.telefono_cliente,
                "empleado": cliente.identificacion_empleado,
                "comentarios": cliente.comentarios
            })

        return Response(data)

    except Exception as e:
        print("ERROR:", str(e))
        return Response({
            "error": str(e)
        }, status=400)
    

@api_view(['POST'])
def crear_cliente(request): 

    # if not validar_permiso(request, 'POST'):
    #     return Response(
    #         {
    #             "error": "No tienes permiso para realizar esta acción"
    #         }, status = 403
    #     )
    
    print("Ya pasé por aquí")

    try:
        campos_obligatorios = [
            'identificacion',
            'nombre',
            'primer_apellido',
            'empleado_id'
        ]

        empleado_id = request.data.get('empleado_id')
        print(f'empleado_id: {empleado_id}')

        for campo in campos_obligatorios:
            if not request.data.get(campo):
                return Response(
                    {
                        "error": f"El campo {campo} es obligatorio"
                    }, status=400
                )
        
        # Datos a validar
        identificacion = request.data.get('identificacion')
        correo = request.data.get('correo')
        empleado_id = request.data.get('empleado_id')
        telefono = request.data.get('telefono')

        # Validar que el cliente no exista
        if Cliente.objects.filter(identificacion_cliente=identificacion).exists():
            return Response(
                {
                    "error": "El cliente ya existe"
                }, status=400
            )
        
        # Validar que el correo sea unico
        if correo:
            if Cliente.objects.filter(correo_cliente=correo).exists():
                return Response(
                    {
                        "error": "El correo ya existe"
                    }, status=400
                )
            
        #Validar longitud del telefono:
        if telefono and len(telefono) > 20:
            return Response(
                {
                    "error": "El telefono es demasiado largo"
                }
            )
        
        # Validar que el empleado si exista
        if not Empleado.objects.filter(identificacion_empleado=empleado_id).exists():
            return Response(
                {
                    "error": "El empleado no existe"
                }, status=400
            )
        
        cliente = Cliente(
            identificacion_cliente = identificacion,
            nombre_cliente = request.data.get('nombre'),
            primer_apellido_cliente = request.data.get('primer_apellido'),
            segundo_apellido_cliente = request.data.get('segundo_apellido'),
            correo_cliente = correo,
            telefono_cliente = telefono,
            identificacion_empleado = empleado_id,
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
    

@api_view(['GET'])
def obtener_cliente(request, id):

    try:
        cliente = Cliente.objects.get(identificacion_cliente=id)

        data = {
            "identificacion": cliente.identificacion_cliente,
            "nombre": cliente.nombre_cliente,
            "primer_apellido": cliente.primer_apellido_cliente,
            "segundo_apellido": cliente.segundo_apellido_cliente,
            "correo": cliente.correo_cliente,
            "telefono": cliente.telefono_cliente,
            "empleado": cliente.identificacion_empleado,
            "comentarios": cliente.comentarios
        }

        return Response(data)
    
    except Cliente.DoesNotExist:
        return Response(
            {
                "error": "El Cliente no existe"
            }, status=400
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )


@api_view(['PUT'])
def actualizar_cliente(request, id):
    try:
        cliente = Cliente.objects.get(identificacion_cliente = id)

        nombre = request.data.get('nombre')
        primer_apellido = request.data.get('primer_apellido')
        segundo_apellido = request.data.get('segundo_apellido')
        correo = request.data.get('correo')
        telefono = request.data.get('telefono')
        comentarios = request.data.get('comentarios')

        # Validar longitud del nombre
        if len(nombre) > 40:
            return Response(
                {
                    "error": "El nombre es demasiado largo"
                }, status=400
            )
        
        # Validar si el correo ya esta siendo utilizado
        if correo:
            if Cliente.objects.filter(correo_cliente=correo)\
                .exclude(identificacion_cliente=id).exists():
                return Response(
                    {
                        "error": "El correo ya esta en uso"
                    }, status=400
                )
            
        # Validar longitud del telefono
        if telefono and len(telefono) > 20:
            return Response(
                {
                    "error": "Telefono demasiado largo"
                }
            )
        
        # Actualización dinámica (solo lo que venga)
        if nombre:
            cliente.nombre_cliente = nombre

        if primer_apellido:
            cliente.primer_apellido_cliente = primer_apellido

        if segundo_apellido:
            cliente.segundo_apellido_cliente = segundo_apellido

        if correo:
            cliente.correo_cliente = correo

        if telefono:
            cliente.telefono_cliente = telefono

        if comentarios:
            cliente.comentarios = comentarios

        cliente.save()

        return Response(
            {
                "mensaje": "Cliente actualizado correctamente"
            }
        )
    
    except Cliente.DoesNotExist:
        return Response (
            {
                "error": "Cliente no encontrado"
            }, status=404
        )
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )


@api_view(['DELETE'])
def eliminar_cliente(request, id):

    try:
        cliente = Cliente.objects.get(identificacion_cliente=id)
        cliente.delete()

        return Response(
            {
                "mensaje": "Cliente eliminado correctamente"
            }
        )

    except Cliente.DoesNotExist:
        return Response(
            {
                "mensaje": "El cliente no existe"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )


@api_view(['GET'])
def listar_empleados(request):

    try:
        nombre = request.query_params.get('nombre')
        correo = request.query_params.get('correo')

        empleados = Empleado.objects.all()

        if nombre:
            empleados = empleados.filter(nombre_empleado__icontains=nombre)

        if correo:
            empleados = empleados.filter(correo_empleado__icontains=correo)

        empleados = empleados.order_by('-identificacion_empleado')

        data = []

        for emp in empleados:
            data.append(
                {
                    "identificacion": emp.identificacion_empleado,
                    "nombre": emp.nombre_empleado,
                    "primer_apellido": emp.primer_apellido_empleado,
                    "segundo_apellido": emp.segundo_apellido_empleado,
                    "correo": emp.correo_empleado,
                    "telefono": emp.telefono_empleado,
                    "direccion": emp.direccion_empleado,
                    "perfil": emp.codigo_perfil_empleado
                }
            )

        return Response(data)
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )


@api_view(['GET'])
def obtener_empleado(request, id):

    try:
        emp = Empleado.objects.get(identificacion_empleado=id)

        data = {
            "identificacion": emp.identificacion_empleado,
            "nombre": emp.nombre_empleado,
            "primer_apellido": emp.primer_apellido_empleado,
            "segundo_apellido": emp.segundo_apellido_empleado,
            "correo": emp.correo_empleado,
            "telefono": emp.telefono_empleado,
            "direccion": emp.direccion_empleado,
            "perfil": emp.codigo_perfil_empleado
        }

        return Response(data)

    except Empleado.DoesNotExist:
        return Response({
            "error": "Empleado no encontrado"
        }, status=404)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=400)

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

        # Verificar cada campo
        for campo in campos_obligatorios:
            if not request.data.get(campo):
                return Response(
                    {
                        "error": f"El campo {campo} es obligatorio"
                    }, status=400
                )
            
        # Validar si el empleado ya existe
        if Empleado.objects.filter(identificacion_empleado=request.data.get('identificacion')).exists():
            return Response(
                {
                    "error": "El empleado ya existe"
                }, status=400
            )
        
        # Validar longitud nombre
        if len(request.data.get('nombre')) > 40:
            return Response(
                    {
                        "error": "Nombre demasiado largo"
                    }, status=400
                )
        
        # Validar longitud de la contraseña
        if len(request.data.get('contrasena')) < 8:
            return Response(
                {
                    "error": "La contraseña debe tener minimo 8 caracteres"
                }, status=400
            )

        # Validar si el correo ya existe
        if Empleado.objects.filter(correo_empleado=request.data.get('correo')).exists():
            return Response(
                {
                    "error": "El correo ya existe"
                }, status=400
            )
            
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


@api_view(['PUT'])
def actualizar_empleado(request, id):
    try:
        emp = Empleado.objects.get(identificacion_empleado = id)

        nombre = request.data.get('nombre')
        correo = request.data.get('correo')
        telefono = request.data.get('telefono')
        direccion = request.data.get('direccion')
        contrasena = request.data.get('contrasena')

        # Validaciones
        if correo:
            if Empleado.objects.filter(correo_empleado=correo)\
                .exclude(identificacion_empleado=id).exists():
                return Response (
                    {
                        "error": "El correo ya está en uso"
                    }, status=400
                )
            
        if contrasena:
            if len(contrasena) < 8:
                return Response(
                    {
                        "error": "La contraseña debe tener minimo 8 caracteres"
                    }, status=400
                )
            
        if nombre:
            emp.nombre_empleado = nombre

        if correo:
            emp.correo_empleado = correo

        if telefono:
            emp.telefono_empleado = telefono

        if direccion:
            emp.direccion_empleado = direccion
        
        if contrasena:
            emp.hash_contrasena_empleado = make_password(contrasena)

        emp.save()

        return Response(
            {
                "mensaje": "Empleado actualizado correctamente"
            }
        )
    
    except Empleado.DoesNotExist:
        return Response(
            {
                "error": "Empleado no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['DELETE'])
def eliminar_empleado(reques, id):
    
    try:
        emp = Empleado.objects.get(identificacion_empleado = id)
        emp.delete()

        return Response(
            {
            "mensaje": "Empleado eliminado correctamente"
            }
        )    
    
    except Empleado.DoesNotExist:
        return Response(
            {
                "error": "Empleado no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    

@api_view(['POST'])
def crear_venta(request):
    try:
        cliente_id = request.data.get('cliente_id')
        empleado_id = request.data.get('empleado_id')
        metodo_pago = request.data.get('metodo_pago')
        productos = request.data.get('productos')

        # Validaciones de campos obligatorios
        if not cliente_id:
            return Response(
                {
                    "error": "El campo 'cliente_id' es obligatorio"
                }, status=400
            )
        
        if not empleado_id:
            return Response(
                {
                    "error": "El campo 'empleado_id' es obligatorio"
                }, status=400
            )
        
        if not metodo_pago:
            return Response(
                {
                    "error": "El campo 'metodo_pago' es obligatorio"
                }, status=400
            )
        
        if not productos:
            return Response(
                {
                    "error": "El campo 'productos' es obligatorio"
                }, status=400
            )
        
        # Validar que productos sea una lista
        if not isinstance(productos, list):
            return Response(
                {
                    "error": "El campo 'productos' debe ser una lista"
                }, status=400
            )
        
        # Validar que la lista de productos no esté vacía
        if len(productos) == 0:
            return Response(
                {
                    "error": "La lista de productos no puede estar vacía"
                }, status=400
            )
        
        # Validar que el cliente existe
        try:
            Cliente.objects.get(identificacion_cliente=cliente_id)
        except Cliente.DoesNotExist:
            return Response(
                {
                    "error": f"El cliente con ID '{cliente_id}' no existe"
                }, status=400
            )
        
        # Validar que el empleado existe
        try:
            Empleado.objects.get(identificacion_empleado=empleado_id)
        except Empleado.DoesNotExist:
            return Response(
                {
                    "error": f"El empleado con ID '{empleado_id}' no existe"
                }, status=400
            )
        
        total = 0
        detalles = []

        for index, item in enumerate(productos):
            # Validar que cada item sea un diccionario
            if not isinstance(item, dict):
                return Response(
                    {
                        "error": f"El producto en posición {index} debe ser un objeto"
                    }, status=400
                )
            
            producto_id = item.get('producto_id')
            cantidad = item.get('cantidad')
            
            # Validar que producto_id existe en el item
            if producto_id is None:
                return Response(
                    {
                        "error": f"El producto en posición {index} no tiene el campo 'producto_id'"
                    }, status=400
                )
            
            # Validar que cantidad existe en el item
            if cantidad is None:
                return Response(
                    {
                        "error": f"El producto en posición {index} no tiene el campo 'cantidad'"
                    }, status=400
                )
            
            # Validar que cantidad sea un número
            try:
                cantidad = float(cantidad)
            except (ValueError, TypeError):
                return Response(
                    {
                        "error": f"La cantidad del producto en posición {index} debe ser un número"
                    }, status=400
                )
            
            # Validar que cantidad sea positiva
            if cantidad <= 0:
                return Response(
                    {
                        "error": f"La cantidad del producto en posición {index} debe ser mayor a 0"
                    }, status=400
                )
            
            # Validar que el producto existe
            try:
                producto = Producto.objects.get(codigo_producto=producto_id)
            except Producto.DoesNotExist:
                return Response(
                    {
                        "error": f"El producto con código '{producto_id}' no existe"
                    }, status=400
                )
            
            # Validar stock del producto
            if producto.controla_stock == 'S':
                if producto.stock_disponible_producto < cantidad:
                    return Response(
                        {
                            "error": f"Stock insuficiente del producto '{producto.nombre_producto}'. Stock disponible: {producto.stock_disponible_producto}, solicitado: {int(cantidad)}"
                        }, status=400
                    )
                
            subtotal = producto.precio_venta_producto * cantidad
            total += subtotal
        
            detalles.append(
                {
                    "producto": producto,
                    "cantidad": cantidad,
                    "precio": producto.precio_venta_producto
                }
            )

        # Obtener siguiente ID de venta
        venta_id = obtener_siguiente_valor('SEQ_VENTAS')

        venta = Venta(
            codigo_venta=venta_id,
            identificacion_cliente_venta = cliente_id,
            identificacion_empleado_venta = empleado_id,
            total_venta = total,
            fecha_venta = date.today(),
            codigo_metodo_pago=metodo_pago
        )

        venta.save()

        # Crear Detalle Ventas
        for d in detalles:
            detalle_id = obtener_siguiente_valor('SEQ_DETALLE_VENTAS')

            DetalleVenta.objects.create(
                codigo_detalle_venta=detalle_id,
                codigo_venta = venta_id,
                codigo_producto = d['producto'].codigo_producto,
                cantidad_producto = d['cantidad'],
                precio_unitario_producto = d['precio']
            )

            # Descontar Stock
            if d['producto'].controla_stock == 'S':
                d['producto'].stock_disponible_producto -= d['cantidad']
                d['producto'].save()

        return Response(
            {
                "mensaje": "Venta Realizada correctamente",
                "venta_id": venta_id,
                "total": total
            }
        )

    except Exception as e:
        return Response (
            {
                "error": str(e)
            }, status=400
        )
        
'''
HECHO VÍA GITHUB COPILOT DESDE VSCODE, POR ESO SE VE TAN ORDENADO Y SIN ERRORES DE SINTAXIS, PERO FUNCIONA PERFECTAMENTE
'''
@api_view(['GET'])
def obtener_venta(request, venta_id):
    try:
        venta = Venta.objects.get(codigo_venta=venta_id)

        detalles = DetalleVenta.objects.filter(codigo_venta=venta_id)

        data_detalles = []

        for d in detalles:
            producto = Producto.objects.get(codigo_producto=d.codigo_producto)

            data_detalles.append(
                {
                    "codigo del producto": producto.codigo_producto,
                    "producto": producto.nombre_producto,
                    "cantidad": d.cantidad_producto,
                    "precio_unitario": d.precio_unitario_producto
                }
            )

        data = {
            "venta_id": venta.codigo_venta,
            "cliente_id": venta.identificacion_cliente_venta,
            "empleado_id": venta.identificacion_empleado_venta,
            "total": venta.total_venta,
            "fecha": venta.fecha_venta,
            "metodo_pago": venta.codigo_metodo_pago,
            "detalles": data_detalles
        }

        return Response(data)

    except Venta.DoesNotExist:
        return Response(
            {
                "error": "Venta no encontrada"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
