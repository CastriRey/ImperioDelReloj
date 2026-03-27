from django.db import models

# =========================
# EMPLEADOS
# =========================
class Empleado(models.Model):
    identificacion_empleado = models.IntegerField(primary_key=True)
    nombre_empleado = models.CharField(max_length=40)
    primer_apellido_empleado = models.CharField(max_length=30)
    segundo_apellido_empleado = models.CharField(max_length=30, null=True, blank=True)

    correo_empleado = models.EmailField(max_length=100, unique=True)
    telefono_empleado = models.CharField(max_length=20)
    direccion_empleado = models.CharField(max_length=100)

    hash_contrasena_empleado = models.CharField(max_length=200)

    codigo_perfil_empleado = models.IntegerField()

    class Meta:
        db_table = 'EMPLEADOS'
        managed = False

    def __str__(self):
        return f"{self.nombre_empleado} {self.primer_apellido_empleado}"
    
# =========================
# CLIENTES
# =========================

class Cliente(models.Model):
    identificacion_cliente = models.IntegerField(primary_key=True)
    nombre_cliente = models.CharField(max_length=40)
    primer_apellido_cliente = models.CharField(max_length=30)
    segundo_apellido_cliente = models.CharField(max_length=30, null=True, blank=True)

    correo_cliente = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    telefono_cliente = models.CharField(max_length=20, null=True, blank=True)

    # fecha_registro_cliente = models.DateField()

    identificacion_empleado = models.IntegerField()

    comentarios = models.CharField(max_length=150, null=True, blank=True)

    # Clave Foranea de la tabla Clientes hacia Empleados por 'identificacion_empleado'
    # empleado = models.ForeignKey(
    #     Empleado,
    #     on_delete=models.DO_NOTHING,
    #     db_column='IDENTIFICACION_EMPLEADO'
    # )

    class Meta:
        db_table = 'CLIENTES'
        managed = False

    def __str__(self):
        return f"{self.nombre_cliente} {self.primer_apellido_cliente}"