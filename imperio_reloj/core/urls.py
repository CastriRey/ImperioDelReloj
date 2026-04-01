from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

# router = DefaultRouter()
# router.register(r'clientes', ClienteViewSet)
# router.register(r'empleados', EmpleadoViewset)

urlpatterns = [
    # path('', include(router.urls)),
    path('login/', login_empleado),
    path('crear-empleado/', crear_empleado),
    path('clientes/', listar_clientes),
    path('clientes/<int:id>', obtener_cliente),
    path('clientes/crear/', crear_cliente),
    path('clientes/<int:id>/actualizar/', actualizar_cliente),
    path('clientes/<int:id>/eliminar/', eliminar_cliente)
]