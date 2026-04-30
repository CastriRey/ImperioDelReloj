from django.db import models

# =========================================================================================
# MÓDULO DE EMPLEADOS
# =========================================================================================
# Este módulo gestiona todos los datos relacionados con empleados del sistema.
# Los empleados son los usuarios autenticados que acceden al sistema con credenciales.

class Empleado(models.Model):
    """
    Modelo que representa un Empleado/Usuario del sistema.
    
    Un empleado es la entidad que tiene acceso al sistema. Cada empleado tiene:
    - Identificación única
    - Datos personales (nombre, apellidos, contacto)
    - Credenciales de autenticación (correo, contraseña)
    - Asignación a un perfil (que define sus permisos)
    
    Atributos:
    - identificacion_empleado: Cédula o documento de identidad (PK)
    - nombre_empleado: Primer nombre del empleado
    - primer_apellido_empleado: Apellido principal
    - segundo_apellido_empleado: Segundo apellido (opcional)
    - correo_empleado: Email único del empleado (usado para login)
    - telefono_empleado: Número de contacto
    - direccion_empleado: Dirección física
    - password: Contraseña hasheada con bcrypt/argon2
    - codigo_perfil_empleado: ID del perfil asignado (determina permisos)
    """
    identificacion_empleado = models.IntegerField(primary_key=True)
    nombre_empleado = models.CharField(max_length=40)
    primer_apellido_empleado = models.CharField(max_length=30)
    segundo_apellido_empleado = models.CharField(max_length=30, null=True, blank=True)

    correo_empleado = models.EmailField(max_length=100, unique=True)
    telefono_empleado = models.CharField(max_length=20)
    direccion_empleado = models.CharField(max_length=100)

    # Campo contraseña: Se usa db_column porque en Oracle se llama de otra forma
    password = models.CharField(max_length=200, db_column='hash_contrasena_empleado')

    # Referencia al perfil del empleado (no es FK porque la tabla es unmanaged)
    codigo_perfil_empleado = models.IntegerField()

    class Meta:
        db_table = 'EMPLEADOS'
        managed = False  # La tabla existe en Oracle, Django no la crea/modifica

    # Métodos de compatibilidad con Django Auth
    @property
    def is_active(self):
        """Indica si el empleado está activo en el sistema"""
        return True

    @property
    def is_staff(self):
        """Indica si es personal administrativo (usado por admin de Django)"""
        return False

    @property
    def is_superuser(self):
        """Indica si es superusuario (usado por admin de Django)"""
        return False

    def has_perm(self, perm, obj=None):
        """Verifica si tiene una permiso específica"""
        return self.is_superuser

    def has_module_perms(self, app_label):
        """Verifica si tiene permisos en un módulo"""
        return self.is_superuser

    @property
    def id(self):
        """Propiedad para compatibilidad con Django: devuelve la identificación"""
        return self.identificacion_empleado

    def __str__(self):
        """Representación en texto del empleado"""
        return f"{self.nombre_empleado} {self.primer_apellido_empleado} ({self.correo_empleado})"
    
# =========================================================================================
# MÓDULO DE CLIENTES
# =========================================================================================
# Este módulo gestiona la información de los clientes que compran en la tienda.

class Cliente(models.Model):
    """
    Modelo que representa un Cliente de la tienda.
    
    Los clientes son las personas naturales o jurídicas que compran productos/servicios.
    Cada cliente tiene:
    - Identificación única
    - Datos personales de contacto
    - Relación con un empleado (quien lo registró/atiende)
    - Historial de compras asociadas
    
    Atributos:
    - identificacion_cliente: Cédula o documento de identidad del cliente (PK)
    - nombre_cliente: Nombre del cliente
    - primer_apellido_cliente: Apellido principal
    - segundo_apellido_cliente: Segundo apellido (opcional)
    - correo_cliente: Email para contacto (único, opcional)
    - telefono_cliente: Teléfono de contacto (opcional)
    - identificacion_empleado: ID del empleado que registró al cliente
    - comentarios: Notas sobre el cliente (límite de 150 caracteres)
    """
    identificacion_cliente = models.IntegerField(primary_key=True)
    nombre_cliente = models.CharField(max_length=40)
    primer_apellido_cliente = models.CharField(max_length=30)
    segundo_apellido_cliente = models.CharField(max_length=30, null=True, blank=True)

    correo_cliente = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    telefono_cliente = models.CharField(max_length=20, null=True, blank=True)

    # ID del empleado que registró/atiende a este cliente
    identificacion_empleado = models.IntegerField()

    # Notas internas sobre el cliente
    comentarios = models.CharField(max_length=150, null=True, blank=True)
    
    class Meta:
        db_table = 'CLIENTES'
        managed = False

    def __str__(self):
        """Representación en texto del cliente"""
        return f"{self.nombre_cliente} {self.primer_apellido_cliente}"

    def obtener_nombre_completo(self):
        """Retorna el nombre completo del cliente"""
        if self.segundo_apellido_cliente:
            return f"{self.nombre_cliente} {self.primer_apellido_cliente} {self.segundo_apellido_cliente}"
        return f"{self.nombre_cliente} {self.primer_apellido_cliente}"

    def obtener_contacto(self):
        """Retorna el mejor contacto disponible"""
        return self.correo_cliente or self.telefono_cliente or "Sin contacto"

    
class RelojCliente(models.Model):
    """
    Modelo que registra los relojes que poseen/traen los clientes.
    
    Esto es importante para el negocio ya que los relojes traen:
    - Garantía
    - Servicio técnico
    - Compras adicionales (repuestos, mantenimiento)
    
    Atributos:
    - codigo_reloj_cliente: ID único del reloj del cliente (PK)
    - codigo_cliente: ID del cliente propietario
    - codigo_marca: Marca del reloj (ejemplo: Rolex, Omega, etc.)
    - modelo: Modelo específico del reloj
    - descripcion_reloj: Descripción detallada del reloj
    """
    codigo_reloj_cliente = models.IntegerField(primary_key=True)
    codigo_cliente = models.IntegerField()
    codigo_marca = models.CharField(max_length=30)
    modelo = models.CharField(max_length=15, null=True, blank=True)
    descripcion_reloj = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = 'RELOJES_CLIENTE'
        managed = False

    def __str__(self):
        """Representación del reloj del cliente"""
        return f"{self.codigo_marca} {self.modelo} - Cliente {self.codigo_cliente}"

    
# =========================================================================================
# MÓDULO DE SEGURIDAD Y PERMISOS
# =========================================================================================
# Este módulo gestiona roles, perfiles, rutas y permisos del sistema.
# Define qué usuario (perfil) puede hacer qué acciones (permisos) en qué partes (rutas).

class Rol(models.Model):
    """
    Modelo que representa un Rol en el sistema.
    
    Un rol es una categoría general de usuario. Ejemplos:
    - Administrador
    - Vendedor
    - Técnico
    - Gerente
    
    Los roles se asignan a Perfiles, y los Perfiles se asignan a Empleados.
    
    Atributos:
    - codigo_rol: ID único del rol (PK)
    - nombre_rol: Nombre descriptivo del rol
    """
    codigo_rol = models.IntegerField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'ROLES'

    def __str__(self):
        """Representación del rol"""
        return self.nombre_rol

    def obtener_perfiles_relacionados(self):
        """Retorna todos los perfiles que usan este rol"""
        return Perfiles.objects.filter(codigo_rol=self.codigo_rol)


class Perfiles(models.Model):
    """
    Modelo que representa un Perfil de usuario en el sistema.
    
    Un perfil es una configuración específica de permisos asignada a empleados.
    Ejemplos de perfiles:
    - Admin Total (acceso a todo)
    - Vendedor Básico (puede ver clientes, crear ventas, ver reportes)
    - Técnico Reparaciones (puede crear servicios, ver relojes)
    
    La relación es:
    Empleado → Perfil → Rol (categoría general)
                    ↓
             Permisos (matriz de acceso a rutas)
    
    Atributos:
    - codigo_perfil: ID único del perfil (PK)
    - nombre_perfil: Nombre descriptivo (ejemplo: "Administrador")
    - codigo_rol: ID del rol asociado (FK)
    """
    codigo_perfil = models.IntegerField(primary_key=True)
    nombre_perfil = models.CharField(max_length=50)
    codigo_rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='codigo_rol')

    class Meta:
        managed = False
        db_table = 'PERFILES'

    def __str__(self):
        """Representación del perfil"""
        return self.nombre_perfil

    def obtener_rol(self):
        """Retorna el rol asociado a este perfil"""
        return self.codigo_rol

    def obtener_permisos(self):
        """Retorna todos los permisos asignados a este perfil"""
        return Permiso.objects.filter(codigo_perfil_permiso=self.codigo_perfil)


class Permiso(models.Model):
    """
    Modelo para gestionar los permisos de perfiles a rutas del sistema.
    
    Esta es la MATRIZ DE CONTROL DE ACCESO del sistema. Define exactamente
    qué perfil puede hacer qué operaciones (CRUD) en qué rutas.
    
    Ejemplo de registro:
    - Perfil: "Vendedor" (código 3)
    - Ruta: "/empleados/" (código 2)
    - Permisos: Consultar=S, Insertar=N, Modificar=N, Eliminar=N
    (Significa: Los vendedores pueden VER empleados pero no crear/editar/eliminar)
    
    Atributos:
    - id: Identificador único auto-generado por Django
    - codigo_perfil_permiso: ID del perfil que tiene estos permisos
    - codigo_ruta_permiso: ID de la ruta/endpoint a proteger
    - insertar: ¿Permite crear (POST) registros?
    - modificar: ¿Permite actualizar (PUT/PATCH) registros?
    - eliminar: ¿Permite borrar (DELETE) registros?
    - consultar: ¿Permite ver (GET) registros?
    """
    # Campo sintético que usa ROWID de Oracle como clave primaria para evitar un ID numérico ausente en la tabla.
    rowid = models.CharField(
        primary_key=True,
        db_column='ROWID',
        max_length=64,
        editable=False
    )

    @property
    def id(self):
        return self.rowid

    # Código del perfil al que se asignan los permisos
    codigo_perfil_permiso = models.IntegerField(
        help_text="ID del perfil que tendrá estos permisos"
    )
    
    # Código de la ruta a la que se asignan los permisos
    codigo_ruta_permiso = models.IntegerField(
        help_text="ID de la ruta/endpoint a proteger"
    )
    
    # Permisos CRUD individuales (S=Sí, N=No)
    insertar = models.CharField(
        max_length=1,
        choices=[('S', 'Sí'), ('N', 'No')],
        default='N',
        help_text="¿Permite insertar/crear registros?"
    )
    modificar = models.CharField(
        max_length=1,
        choices=[('S', 'Sí'), ('N', 'No')],
        default='N',
        help_text="¿Permite modificar registros?"
    )
    eliminar = models.CharField(
        max_length=1,
        choices=[('S', 'Sí'), ('N', 'No')],
        default='N',
        help_text="¿Permite eliminar registros?"
    )
    consultar = models.CharField(
        max_length=1,
        choices=[('S', 'Sí'), ('N', 'No')],
        default='S',
        help_text="¿Permite ver/consultar registros?"
    )

    class Meta:
        managed = False
        db_table = 'PERMISOS'
        # La combinación de perfil + ruta debe ser única (un perfil no puede tener dos conjuntos de permisos para la misma ruta)
        unique_together = ('codigo_perfil_permiso', 'codigo_ruta_permiso')

    def __str__(self):
        """Retorna una descripción legible del permiso"""
        perfil_obj = Perfiles.objects.filter(codigo_perfil=self.codigo_perfil_permiso).first()
        ruta_obj = Ruta.objects.filter(codigo_ruta=self.codigo_ruta_permiso).first()
        perfil_nombre = perfil_obj.nombre_perfil if perfil_obj else f"Perfil {self.codigo_perfil_permiso}"
        ruta_nombre = ruta_obj.url_ruta if ruta_obj else f"Ruta {self.codigo_ruta_permiso}"
        return f"Permiso: {perfil_nombre} -> {ruta_nombre}"

    def tiene_permiso_consultar(self):
        """¿Permite consultar (leer) registros?"""
        return self.consultar == 'S'

    def tiene_permiso_insertar(self):
        """¿Permite insertar (crear) registros?"""
        return self.insertar == 'S'

    def tiene_permiso_modificar(self):
        """¿Permite modificar registros?"""
        return self.modificar == 'S'

    def tiene_permiso_eliminar(self):
        """¿Permite eliminar registros?"""
        return self.eliminar == 'S'


class Ruta(models.Model):
    """
    Modelo que representa una Ruta/Endpoint del sistema que se puede proteger.
    
    Una ruta es una dirección URL en el sistema. Ejemplos:
    - /empleados/
    - /productos/
    - /clientes/
    - /seguridad/permisos/
    
    Las rutas se vinculan a Permisos para controlar quién puede acceder.
    
    Atributos:
    - codigo_ruta: ID único de la ruta (PK)
    - nombre_ruta: Nombre descriptivo (ejemplo: "Gestión de Empleados")
    - url_ruta: URL exacta (ejemplo: "/empleados/")
    """
    codigo_ruta = models.IntegerField(primary_key=True)
    nombre_ruta = models.CharField(max_length=50)
    url_ruta = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'RUTAS'

    def __str__(self):
        """Retorna la URL de la ruta para visualización en formularios"""
        return self.url_ruta

    def obtener_nombre_descriptivo(self):
        """Retorna el nombre descriptivo de la ruta"""
        return self.nombre_ruta

    def obtener_permisos(self):
        """Retorna todos los permisos asignados a esta ruta"""
        return Permiso.objects.filter(codigo_ruta_permiso=self.codigo_ruta)


# =========================================================================================
# MÓDULO DE PRODUCTOS
# =========================================================================================
# Este módulo gestiona los productos que se venden en la tienda.

class TipoProducto(models.Model):
    """
    Modelo que representa un Tipo de Producto en el sistema.
    
    Los tipos de producto son categorías de lo que se vende:
    - Relojes completos
    - Repuestos (cristal, correa, batería, etc.)
    - Servicios (limpieza, reparación)
    - Accesorios
    
    Permite categorizar y agrupar productos por tipo.
    
    Atributos:
    - codigo_tipo_producto: ID único del tipo (PK)
    - nombre_tipo_producto: Nombre descriptivo (ejemplo: "Relojes")
    """
    codigo_tipo_producto = models.IntegerField(primary_key=True)
    nombre_tipo_producto = models.CharField(max_length=40)

    class Meta:
        db_table = 'TIPO_PRODUCTOS'
        managed = False

    def __str__(self):
        """Representación del tipo de producto"""
        return self.nombre_tipo_producto

    def obtener_productos(self):
        """Retorna todos los productos de este tipo"""
        return Producto.objects.filter(codigo_tipo_producto=self.codigo_tipo_producto)

    def contar_productos(self):
        """Retorna la cantidad de productos en este tipo"""
        return self.obtener_productos().count()


class Marca(models.Model):
    """
    Modelo que representa una Marca de productos.
    
    Las marcas son fabricantes de relojes y accesorios:
    - Rolex
    - Omega
    - TAG Heuer
    - Bulova
    - etc.
    
    Atributos:
    - codigo_marca: ID único de la marca (PK)
    - nombre_marca: Nombre de la marca
    """
    codigo_marca = models.IntegerField(primary_key=True)
    nombre_marca = models.CharField(max_length=20)

    class Meta:
        db_table = 'MARCAS'
        managed = False

    def __str__(self):
        """Representación de la marca"""
        return self.nombre_marca

    def obtener_productos(self):
        """Retorna todos los productos de esta marca"""
        return Producto.objects.filter(codigo_marca=self.codigo_marca)


class Producto(models.Model):
    """
    Modelo que representa un Producto en la tienda.
    
    Los productos son los artículos que se venden: relojes, repuestos, servicios, etc.
    Cada producto tiene:
    - Información básica (nombre, marca, tipo)
    - Precios (venta, costo)
    - Control de inventario (stock, stock mínimo)
    - Información de garantía y última actualización
    
    Atributos:
    - codigo_producto: ID único del producto (PK)
    - nombre_producto: Nombre descriptivo (ejemplo: "Reloj Rolex Submariner")
    - codigo_marca: ID de la marca fabricante
    - codigo_tipo_producto: ID del tipo de producto
    - modelo_producto: Modelo específico (ejemplo: "116610")
    - precio_venta_producto: Precio de venta al público
    - costo_producto: Costo de adquisición
    - garantia_producto: Meses de garantía
    - descripcion_producto: Descripción técnica detallada
    - stock_disponible_producto: Cantidad actual en inventario
    - stock_minimo_producto: Cantidad mínima (alerta si baja de esto)
    - controla_stock: ¿Se controla este producto? (S/N)
    - ultima_actualizacion_producto: Última fecha de cambio de precio/stock
    """
    codigo_producto = models.IntegerField(primary_key=True)
    nombre_producto = models.CharField(max_length=40)
    codigo_marca = models.IntegerField(max_length=3)
    codigo_tipo_producto = models.IntegerField(max_length=2)
    modelo_producto = models.CharField(max_length=15, null=True, blank=True)
    precio_venta_producto = models.DecimalField(max_digits=10, decimal_places=2)
    costo_producto = models.DecimalField(max_digits=10, decimal_places=2)
    garantia_producto = models.IntegerField(max_length=2)
    descripcion_producto = models.CharField(max_length=255, null=True, blank=True)
    stock_disponible_producto = models.IntegerField(max_length=3)
    stock_minimo_producto = models.IntegerField(max_length=3)
    controla_stock = models.CharField(max_length=1)
    ultima_actualizacion_producto = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'PRODUCTOS'
        managed = False

    def __str__(self):
        """Representación del producto"""
        return f"{self.nombre_producto} ({self.modelo_producto})" if self.modelo_producto else self.nombre_producto

    def obtener_nombre_completo(self):
        """Retorna nombre completo con marca y modelo"""
        marca = Marca.objects.filter(codigo_marca=self.codigo_marca).first()
        marca_nombre = marca.nombre_marca if marca else "Marca desconocida"
        if self.modelo_producto:
            return f"{marca_nombre} {self.nombre_producto} {self.modelo_producto}"
        return f"{marca_nombre} {self.nombre_producto}"

    def obtener_tipo(self):
        """Retorna el nombre del tipo de producto asociado."""
        tipo = TipoProducto.objects.filter(codigo_tipo_producto=self.codigo_tipo_producto).first()
        return tipo.nombre_tipo_producto if tipo else "Tipo desconocido"

    def obtener_marca(self):
        """Retorna el nombre de la marca asociada al producto."""
        marca = Marca.objects.filter(codigo_marca=self.codigo_marca).first()
        return marca.nombre_marca if marca else "Marca desconocida"

    def obtener_ganancia(self):
        """Calcula la ganancia (diferencia entre precio de venta y costo)"""
        return self.precio_venta_producto - self.costo_producto

    def obtener_margen_ganancia(self):
        """Calcula el margen de ganancia en porcentaje"""
        if self.costo_producto == 0:
            return 0
        return ((self.precio_venta_producto - self.costo_producto) / self.costo_producto) * 100

    def necesita_reorden(self):
        """¿Necesita reordenarse? (stock actual está por debajo del mínimo)"""
        return self.stock_disponible_producto < self.stock_minimo_producto

    def esta_activo(self):
        """¿El producto está activo para la venta?"""
        return self.controla_stock == 'S'


# =========================================================================================
# MÓDULO DE VENTAS
# =========================================================================================
# Este módulo gestiona las ventas y facturas de la tienda.

class Venta(models.Model):
    """
    Modelo que representa una Venta/Factura.
    
    Cada venta registra una transacción completa:
    - Qué cliente compró
    - Quién lo vendió (empleado)
    - Cuándo se realizó
    - Cuánto fue el total
    - Cómo pagó
    
    Atributos:
    - codigo_venta: ID único de la venta/factura (PK)
    - identificacion_cliente_venta: ID del cliente
    - identificacion_empleado_venta: ID del empleado que realizó la venta
    - total_venta: Monto total de la transacción
    - fecha_venta: Fecha de la venta
    - codigo_metodo_pago: Método de pago usado (efectivo, tarjeta, etc.)
    """
    codigo_venta = models.IntegerField(primary_key=True)
    identificacion_cliente_venta = models.IntegerField()
    identificacion_empleado_venta = models.IntegerField()
    total_venta = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateField()
    codigo_metodo_pago = models.IntegerField()

    class Meta:
        db_table = 'VENTAS'
        managed = False

    def __str__(self):
        """Representación de la venta"""
        return f"Venta #{self.codigo_venta} - ${self.total_venta}"


class DetalleVenta(models.Model):
    """
    Modelo que representa los ítems/productos en una Venta.
    
    Cada detalle de venta es una línea en una factura:
    - Qué producto se vendió
    - Cuántos se vendieron
    - A qué precio unitario
    
    Una venta puede tener múltiples detalles de venta.
    
    Atributos:
    - codigo_detalle_venta: ID único del detalle (PK)
    - codigo_venta: ID de la venta a la que pertenece
    - codigo_producto: ID del producto vendido
    - cantidad_producto: Cuántos se vendieron
    - precio_unitario_producto: Precio por unidad
    """
    codigo_detalle_venta = models.IntegerField(primary_key=True)
    codigo_venta = models.IntegerField()
    codigo_producto = models.IntegerField()
    cantidad_producto = models.IntegerField()
    precio_unitario_producto = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'DETALLE_VENTAS'
        managed = False

    def __str__(self):
        """Representación del detalle"""
        return f"Detalle Venta #{self.codigo_detalle_venta} - Venta #{self.codigo_venta}"

    def obtener_subtotal(self):
        """Calcula el subtotal de esta línea (cantidad × precio)"""
        return self.cantidad_producto * self.precio_unitario_producto


# =========================================================================================
# MÓDULO DE SERVICIOS
# =========================================================================================
# Este módulo gestiona los servicios técnicos (reparaciones) de relojes.

class TipoServicio(models.Model):
    """
    Modelo que representa tipos de Servicios disponibles.
    
    Tipos de servicios:
    - Limpieza
    - Reparación
    - Cambio de batería
    - Cambio de correa
    - Revisión general
    
    Atributos:
    - codigo_tipo_servicio: ID único (PK)
    - nombre_tipo_servicio: Nombre descriptivo
    """
    codigo_tipo_servicio = models.IntegerField(primary_key=True)
    nombre_tipo_servicio = models.CharField(max_length=30)

    class Meta:
        db_table = 'TIPOS_SERVICIO'
        managed = False

    def __str__(self):
        """Representación del tipo de servicio"""
        return self.nombre_tipo_servicio


class EstadoServicio(models.Model):
    """
    Modelo que representa estados posibles de un Servicio.
    
    Estados:
    - Recibido (acaba de llegar)
    - En reparación
    - Reparado
    - Completado/Entregado
    - Rechazado
    
    Atributos:
    - codigo_estado_servicio: ID único (PK)
    - nombre_estado_reparacion: Nombre del estado
    """
    codigo_estado_servicio = models.IntegerField(primary_key=True)
    nombre_estado_reparacion = models.CharField(max_length=20)

    class Meta:
        db_table = 'ESTADOS_SERVICIO'
        managed = False

    def __str__(self):
        """Representación del estado"""
        return self.nombre_estado_reparacion


class Servicio(models.Model):
    """
    Modelo que representa un Servicio Técnico (Reparación) de un reloj.
    
    Cuando un cliente trae un reloj a reparar, se crea un registro de servicio
    que sigue el proceso de diagnóstico, reparación y entrega.
    
    Atributos:
    - codigo_servicio: ID único del servicio (PK)
    - codigo_tecnico: ID del empleado técnico que realiza el servicio
    - codigo_tipo_servicio: Tipo de servicio a realizar
    - codigo_estado_servicio: Estado actual del servicio
    - codigo_detalle_venta: Factura relacionada (opcional)
    - codigo_reloj_cliente: El reloj siendo reparado
    - fecha_servicio: Fecha del servicio
    - descripcion_falla: Descripción de qué tiene la falla
    """
    codigo_servicio = models.IntegerField(primary_key=True)
    codigo_tecnico = models.IntegerField()
    codigo_tipo_servicio = models.IntegerField()
    codigo_estado_servicio = models.IntegerField()
    codigo_detalle_venta = models.IntegerField(null=True, blank=True)
    codigo_reloj_cliente = models.IntegerField()
    fecha_servicio = models.DateField()
    descripcion_falla = models.CharField(max_length=500)

    class Meta:
        db_table = 'SERVICIOS'
        managed = False

    def __str__(self):
        """Representación del servicio"""
        return f"Servicio #{self.codigo_servicio} - Reloj {self.codigo_reloj_cliente}"


class MetodoPago(models.Model):
    """
    Modelo que representa Métodos de Pago disponibles.
    
    Métodos:
    - Efectivo
    - Tarjeta de Crédito
    - Tarjeta de Débito
    - Transferencia
    
    Atributos:
    - codigo_metodo_pago: ID único (PK)
    - nombre_metodo_pago: Nombre del método
    """
    codigo_metodo_pago = models.IntegerField(primary_key=True)
    nombre_metodo_pago = models.CharField(max_length=30)

    class Meta:
        db_table = 'METODOS_PAGO'
        managed = False