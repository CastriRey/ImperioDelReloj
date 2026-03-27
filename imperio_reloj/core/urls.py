from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, EmpleadoViewset, listar_clientes




router = DefaultRouter()
router.register(r'clientes', ClienteViewSet)
router.register(r'empleados', EmpleadoViewset)

urlpatterns = [
    path('', include(router.urls)),
    path('clientes/', listar_clientes,)
]