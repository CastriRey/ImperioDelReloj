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
        return f"{self.nombre_empleado} {self.primer_apellido_empleado} {self.correo_empleado}"
    
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
    
# =========================
# PERFILES, RUTAS Y PERMISOS
# =========================

class Perfiles(models.Model):
    codigo_perfil = models.IntegerField(primary_key=True)
    nombre_perfil = models.CharField(max_length=50)
    codigo_rol = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'PERFILES'

class Permiso(models.Model):
    codigo_perfil_permiso = models.IntegerField(primary_key=True)
    codigo_ruta_permiso = models.IntegerField()
    insertar = models.CharField(max_length=1)
    modificar = models.CharField(max_length=1)
    eliminar = models.CharField(max_length=1)
    consultar = models.CharField(max_length=1)

    class Meta:
        managed = False
        db_table = 'PERMISOS'

class Ruta(models.Model):
    codigo_ruta = models.IntegerField(primary_key=True)
    nombre_ruta = models.CharField(max_length=50)
    url_ruta = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'RUTAS'


# =========================
# PRODUCTOS
# =========================
class Producto(models.Model):
    codigo_producto = models.IntegerField(primary_key=True)
    nombre_producto = models.CharField(max_length=40)
    precio_venta_producto = models.DecimalField(max_digits=10, decimal_places=2)
    stock_disponible_producto = models.IntegerField(max_length=3)
    controla_stock = models.CharField(max_length=1)

    class Meta:
        db_table = 'PRODUCTOS'
        managed = False

class TipoProducto(models.Model):
    codigo_tipo_producto = models.IntegerField(primary_key=True)
    nombre_tipo_producto = models.CharField(max_length=40)

    class Meta:
        db_table = 'TIPO_PRODUCTOS'
        managed = False

class Marca(models.Model):
    codigo_marca = models.IntegerField(primary_key=True)
    nombre_marca = models.CharField(max_length=20)

    class Meta:
        db_table = 'MARCAS'
        managed = False

# =========================
# VENTAS
# =========================
class Venta(models.Model):
    codigo_venta = models.IntegerField(primary_key=True)
    identificacion_cliente_venta = models.IntegerField()
    identificacion_empleado_venta = models.IntegerField()
    total_venta = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateField()
    codigo_metodo_pago = models.IntegerField()

    class Meta:
        db_table = 'VENTAS'
        managed = False

# =========================
# DETALLE VENTAS
# =========================
class DetalleVenta(models.Model):
    codigo_detalle_venta = models.IntegerField(primary_key=True)
    codigo_venta = models.IntegerField()
    codigo_producto = models.IntegerField()
    cantidad_producto = models.IntegerField()
    precio_unitario_producto = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'DETALLE_VENTAS'
        managed = False
