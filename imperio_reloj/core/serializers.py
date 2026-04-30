from rest_framework import serializers
from .models import Cliente, Empleado
from django.contrib.auth.hashers import make_password

# Crear el HASH de contrasena
def create(self, validated_data):
    validated_data['password'] = make_password(
        validated_data['password']
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
        extra_kwargs = {
            'password': {'write_only': True}
        }

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'