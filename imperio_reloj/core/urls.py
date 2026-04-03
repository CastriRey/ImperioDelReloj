from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

# router = DefaultRouter()
# router.register(r'clientes', ClienteViewSet)
# router.register(r'empleados', EmpleadoViewset)

urlpatterns = [
    # path('', include(router.urls)),
    path('login/', login_empleado),
    path('clientes/', listar_clientes),
    path('clientes/crear/', crear_cliente),
    path('clientes/<int:id>/', obtener_cliente),
    path('clientes/<int:id>/actualizar/', actualizar_cliente),
    path('clientes/<int:id>/eliminar/', eliminar_cliente),
    path('empleados/', listar_empleados),
    path('empleados/crear/', crear_empleado),
    path('empleados/<int:id>/', obtener_empleado),
    path('empleados/<int:id>/actualizar/', actualizar_empleado),
    path('empleados/<int:id>/eliminar/', eliminar_empleado),
    path('ventas/', listar_ventas),
    path('ventas/crear/', crear_venta),
    path('ventas/<int:venta_id>/', obtener_venta),
    path('tipos_producto/', listar_tipos_producto),
    path('tipos_producto/crear/', crear_tipo_producto),
    path('tipos_producto/<int:codigo>/', obtener_tipo_producto),
    path('tipos_producto/<int:codigo>/actualizar/', actualizar_tipo_producto),
    path('tipos_producto/<int:codigo>/eliminar/', eliminar_tipo_producto),
    path('marcas/', listar_marcas),
    path('marcas/crear/', crear_marca),
    path('marcas/<int:codigo>/', obtener_marca),
    path('marcas/<int:codigo>/actualizar/', actualizar_marca),
    path('marcas/<int:codigo>/eliminar/', eliminar_marca),
]