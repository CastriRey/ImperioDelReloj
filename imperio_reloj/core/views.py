from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Cliente, Empleado
from .serializers import ClienteSerializer, EmpleadoSerializer

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
