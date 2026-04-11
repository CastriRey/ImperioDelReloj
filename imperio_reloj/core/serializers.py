from rest_framework import serializers
from .models import Cliente, Empleado, Servicio
from django.contrib.auth.hashers import make_password

'''
Un Serializer convierte los objetos de Python en JSON viceversa
'''

# Crear el HASH de contrasena
def create(self, validated_data):
    validated_data['hash_contrasena_empleado'] = make_password(
        validated_data['hash_contrasena_empleado']
    )
    return super().create(validated_data)

# Validar que la identificacion_cliente no exista en la base de datos
def validate_identificacion_cliente(self, value):
    if Cliente.objects.filter(identificacion_cliente=value).exists():
        raise serializers.ValidationError("Ya existe un cliente con esa identificación")
    return value


class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = '__all__'

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = '__all__'