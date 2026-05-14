from django.shortcuts import render, get_object_or_404, redirect
from django import forms
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from .models import *
from .serializers import ClienteSerializer, EmpleadoSerializer
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.db import connection
from .utils.permissions import PermisoDinamico
from .utils.authentication import CustomJWTAuthentication
from datetime import date, datetime

# Create your views here.

'''
# Que hacen los ModelViewSet?
Los ModelViewSet nos crea automaticamente los metodos
get, post, put, delete para no tener que escribir codigo extra
'''

class EmpleadoViewset(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    permission_classes = [PermisoDinamico]

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [PermisoDinamico]


def login_view(request):
    return render(request, 'core/login.html')


def dashboard(request):
    return render(request, 'core/dashboard.html')


class EmpleadoForm(forms.ModelForm):
    # Campo visible para el nombre del perfil, con escritura y lista sugerida
    profile_name = forms.CharField(
        required=True,
        label='Perfil',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'perfiles_list',
            'placeholder': 'Escribe o selecciona un perfil',
        })
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False, help_text="Deja vacío para mantener la contraseña actual")

    class Meta:
        model = Empleado
        fields = ['identificacion_empleado', 'nombre_empleado', 'primer_apellido_empleado', 'segundo_apellido_empleado', 'correo_empleado', 'telefono_empleado', 'direccion_empleado', 'password', 'codigo_perfil_empleado']
        widgets = {
            'identificacion_empleado': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_empleado': forms.TextInput(attrs={'class': 'form-control'}),
            'primer_apellido_empleado': forms.TextInput(attrs={'class': 'form-control'}),
            'segundo_apellido_empleado': forms.TextInput(attrs={'class': 'form-control'}),
            'correo_empleado': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono_empleado': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion_empleado': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_perfil_empleado': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El campo código de perfil se maneja internamente, el usuario ve solo el nombre
        self.fields['codigo_perfil_empleado'].required = False
        if self.instance and self.instance.pk:
            perfil = Perfiles.objects.filter(codigo_perfil=self.instance.codigo_perfil_empleado).first()
            self.initial['profile_name'] = perfil.nombre_perfil if perfil else ''

    def clean_profile_name(self):
        nombre = self.cleaned_data.get('profile_name')
        perfil = Perfiles.objects.filter(nombre_perfil__iexact=nombre).first()
        if not perfil:
            raise forms.ValidationError('Perfil no válido. Selecciona uno de los perfiles existentes.')
        self.cleaned_data['codigo_perfil_empleado'] = perfil.codigo_perfil
        return nombre


def empleados_list(request):
    empleados = Empleado.objects.all()
    return render(request, 'core/empleados_list.html', {'empleados': empleados})


def empleado_create(request):
    # Vista para crear un empleado desde interfaz.
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            empleado = form.save(commit=False)
            if form.cleaned_data['password']:
                empleado.password = make_password(form.cleaned_data['password'])
            empleado.save()
            return redirect('empleados_list')
    else:
        form = EmpleadoForm()
    perfiles = Perfiles.objects.all()
    return render(request, 'core/empleado_form.html', {'form': form, 'title': 'Crear Empleado', 'perfiles': perfiles})


def empleado_edit(request, pk):
    # Vista para editar un empleado, manteniendo estilos Bootstrap.
    empleado = get_object_or_404(Empleado, pk=pk)
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            emp = form.save(commit=False)
            if form.cleaned_data['password']:
                emp.password = make_password(form.cleaned_data['password'])
            emp.save()
            return redirect('empleados_list')
    else:
        form = EmpleadoForm(instance=empleado)
        form.fields['password'].required = False
    perfiles = Perfiles.objects.all()
    return render(request, 'core/empleado_form.html', {'form': form, 'title': 'Editar Empleado', 'perfiles': perfiles})


def empleado_delete(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    if request.method == 'POST':
        empleado.delete()
        return redirect('empleados_list')
    return render(request, 'core/empleado_confirm_delete.html', {'empleado': empleado})


def seguridad(request):
    return render(request, 'core/seguridad.html')


class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['codigo_rol', 'nombre_rol']
        widgets = {
            'codigo_rol': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_rol': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfiles
        fields = ['codigo_perfil', 'nombre_perfil', 'codigo_rol']
        widgets = {
            'codigo_perfil': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_perfil': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_rol': forms.Select(attrs={'class': 'form-select'}),
        }


class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = ['codigo_ruta', 'nombre_ruta', 'url_ruta']
        widgets = {
            'codigo_ruta': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_ruta': forms.TextInput(attrs={'class': 'form-control'}),
            'url_ruta': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PermisoForm(forms.ModelForm):
    YES_NO_CHOICES = [('S', 'Sí'), ('N', 'No')]

    codigo_perfil_permiso = forms.ModelChoiceField(
        queryset=Perfiles.objects.all(),
        to_field_name='codigo_perfil',
        empty_label=None,
        label='Perfil',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    codigo_ruta_permiso = forms.ModelChoiceField(
        queryset=Ruta.objects.all(),
        to_field_name='codigo_ruta',
        empty_label=None,
        label='Ruta',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    insertar = forms.ChoiceField(choices=YES_NO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    modificar = forms.ChoiceField(choices=YES_NO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    eliminar = forms.ChoiceField(choices=YES_NO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    consultar = forms.ChoiceField(choices=YES_NO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    def clean_codigo_perfil_permiso(self):
        perfil = self.cleaned_data.get('codigo_perfil_permiso')
        return perfil.codigo_perfil if perfil else None

    def clean_codigo_ruta_permiso(self):
        ruta = self.cleaned_data.get('codigo_ruta_permiso')
        return ruta.codigo_ruta if ruta else None

    class Meta:
        model = Permiso
        fields = ['codigo_perfil_permiso', 'codigo_ruta_permiso', 'insertar', 'modificar', 'eliminar', 'consultar']


def roles_list(request):
    roles = Rol.objects.all()
    return render(request, 'core/roles_list.html', {'roles': roles})


def rol_create(request):
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('roles_list')
    else:
        form = RolForm()
    return render(request, 'core/rol_form.html', {'form': form, 'title': 'Crear Rol'})


def rol_edit(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == 'POST':
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            form.save()
            return redirect('roles_list')
    else:
        form = RolForm(instance=rol)
    return render(request, 'core/rol_form.html', {'form': form, 'title': 'Editar Rol'})


def rol_delete(request, pk):
    rol = get_object_or_404(Rol, pk=pk)
    if request.method == 'POST':
        rol.delete()
        return redirect('roles_list')
    return render(request, 'core/rol_confirm_delete.html', {'rol': rol})


def perfiles_list(request):
    perfiles = Perfiles.objects.all()
    return render(request, 'core/perfiles_list.html', {'perfiles': perfiles})


def perfil_create(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('perfiles_list')
    else:
        form = PerfilForm()
    return render(request, 'core/perfil_form.html', {'form': form, 'title': 'Crear Perfil'})


def perfil_edit(request, pk):
    perfil = get_object_or_404(Perfiles, pk=pk)
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            return redirect('perfiles_list')
    else:
        form = PerfilForm(instance=perfil)
    return render(request, 'core/perfil_form.html', {'form': form, 'title': 'Editar Perfil'})


def perfil_delete(request, pk):
    perfil = get_object_or_404(Perfiles, pk=pk)
    if request.method == 'POST':
        perfil.delete()
        return redirect('perfiles_list')
    return render(request, 'core/perfil_confirm_delete.html', {'perfil': perfil})


def rutas_list(request):
    rutas = Ruta.objects.all()
    return render(request, 'core/rutas_list.html', {'rutas': rutas})


def ruta_create(request):
    if request.method == 'POST':
        form = RutaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('rutas_list')
    else:
        form = RutaForm()
    return render(request, 'core/ruta_form.html', {'form': form, 'title': 'Crear Ruta'})


def ruta_edit(request, pk):
    ruta = get_object_or_404(Ruta, pk=pk)
    if request.method == 'POST':
        form = RutaForm(request.POST, instance=ruta)
        if form.is_valid():
            form.save()
            return redirect('rutas_list')
    else:
        form = RutaForm(instance=ruta)
    return render(request, 'core/ruta_form.html', {'form': form, 'title': 'Editar Ruta'})


def ruta_delete(request, pk):
    ruta = get_object_or_404(Ruta, pk=pk)
    if request.method == 'POST':
        ruta.delete()
        return redirect('rutas_list')
    return render(request, 'core/ruta_confirm_delete.html', {'ruta': ruta})


def permisos_list(request):
    permisos = Permiso.objects.all()
    permisos_mostrados = []
    for permiso in permisos:
        perfil_obj = Perfiles.objects.filter(codigo_perfil=permiso.codigo_perfil_permiso).first()
        ruta_obj = Ruta.objects.filter(codigo_ruta=permiso.codigo_ruta_permiso).first()
        permisos_mostrados.append({
            'codigo_perfil_permiso': permiso.codigo_perfil_permiso,
            'perfil_nombre': perfil_obj.nombre_perfil if perfil_obj else f'Perfil {permiso.codigo_perfil_permiso}',
            'codigo_ruta_permiso': permiso.codigo_ruta_permiso,
            'ruta_url': ruta_obj.url_ruta if ruta_obj else f'Ruta {permiso.codigo_ruta_permiso}',
            'insertar': permiso.insertar,
            'modificar': permiso.modificar,
            'eliminar': permiso.eliminar,
            'consultar': permiso.consultar,
        })
    return render(request, 'core/permisos_list.html', {'permisos': permisos_mostrados})


def permiso_create(request):
    if request.method == 'POST':
        form = PermisoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('permisos_list')
    else:
        form = PermisoForm()
    return render(request, 'core/permiso_form.html', {'form': form, 'title': 'Crear Permiso'})


def permiso_edit(request, perfil_id, ruta_id):
    # Vista para editar un permiso usando perfil_id y ruta_id como clave compuesta.
    permiso = get_object_or_404(Permiso, codigo_perfil_permiso=perfil_id, codigo_ruta_permiso=ruta_id)
    if request.method == 'POST':
        form = PermisoForm(request.POST, instance=permiso)
        if form.is_valid():
            form.save()
            return redirect('permisos_list')
    else:
        form = PermisoForm(instance=permiso)
    return render(request, 'core/permiso_form.html', {'form': form, 'title': 'Editar Permiso'})


def permiso_delete(request, perfil_id, ruta_id):
    # Vista para eliminar un permiso usando perfil_id y ruta_id como clave compuesta.
    permiso = get_object_or_404(Permiso, codigo_perfil_permiso=perfil_id, codigo_ruta_permiso=ruta_id)
    if request.method == 'POST':
        permiso.delete()
        return redirect('permisos_list')
    return render(request, 'core/permiso_confirm_delete.html', {'permiso': permiso})


def logout_view(request):
    return render(request, 'core/logout.html')


# =========================================================================================
# CRUD: CLIENTES (Interfaz Web)
# =========================================================================================

class ClienteForm(forms.ModelForm):
    """
    Formulario para crear y editar clientes en la interfaz web.
    
    Este formulario maneja:
    - Datos personales del cliente (nombre, apellidos)
    - Datos de contacto (correo, teléfono)
    - Comentarios internos
    
    El empleado asignado se establece automáticamente con el usuario logueado.
    """

    class Meta:
        model = Cliente
        fields = ['identificacion_cliente', 'nombre_cliente', 'primer_apellido_cliente', 
                 'segundo_apellido_cliente', 'correo_cliente', 'telefono_cliente', 'comentarios']
        widgets = {
            'identificacion_cliente': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'primer_apellido_cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'segundo_apellido_cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'correo_cliente': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono_cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'comentarios': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


def clientes_list(request):
    """
    Vista que lista todos los clientes registrados.
    
    Muestra una tabla con los datos principales de cada cliente.
    Permite editar, eliminar y crear nuevos clientes.
    """
    clientes = Cliente.objects.all()
    return render(request, 'core/clientes_list.html', {'clientes': clientes})


def cliente_create(request):
    """
    Vista para crear un nuevo cliente.
    
    - GET: Muestra el formulario en blanco
    - POST: Guarda el cliente si el formulario es válido
    
    El empleado asignado se obtiene automáticamente del usuario logueado.
    """
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            # Asignar automáticamente el empleado actual
            identificacion_empleado = request.POST.get('identificacion_empleado') or request.COOKIES.get('user_id') or request.session.get('user_id')
            if identificacion_empleado:
                cliente.identificacion_empleado = int(identificacion_empleado)
                cliente.save()
                return redirect('clientes_list')
            else:
                form.add_error(None, 'No se pudo determinar el empleado que registra el cliente. Por favor, inicia sesión de nuevo.')
    else:
        form = ClienteForm()
    return render(request, 'core/cliente_form.html', {'form': form, 'title': 'Crear Cliente'})


def cliente_edit(request, pk):
    """
    Vista para editar un cliente existente.
    
    - GET: Muestra el formulario con los datos actuales del cliente
    - POST: Actualiza el cliente si el formulario es válido
    
    Al guardar, se actualiza el empleado asignado con el usuario actual.
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save(commit=False)
            identificacion_empleado = request.POST.get('identificacion_empleado') or request.COOKIES.get('user_id') or request.session.get('user_id')
            if identificacion_empleado:
                cliente.identificacion_empleado = int(identificacion_empleado)
            cliente.save()
            return redirect('clientes_list')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'core/cliente_form.html', {'form': form, 'title': 'Editar Cliente'})


def cliente_delete(request, pk):
    """
    Vista para eliminar un cliente.
    
    - GET: Muestra página de confirmación
    - POST: Elimina el cliente definitivamente
    """
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('clientes_list')
    return render(request, 'core/cliente_confirm_delete.html', {'cliente': cliente})


# =========================================================================================
# CRUD: RELOJES DEL CLIENTE (Interfaz Web)
# =========================================================================================

class RelojClienteForm(forms.ModelForm):
    """
    Formulario para crear y editar relojes de un cliente.
    
    Permite registrar los relojes que han pasado por el negocio.
    """
    # Campo visible para buscar/seleccionar marca
    marca_search = forms.CharField(
        required=True,
        label='Marca',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar marca...',
        })
    )

    class Meta:
        model = RelojCliente
        fields = ['codigo_marca', 'modelo', 'descripcion_reloj']
        widgets = {
            'codigo_marca': forms.HiddenInput(),  # Campo oculto para el ID real
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Submariner, Speedmaster'}),
            'descripcion_reloj': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción detallada del reloj'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cuando se edita, establecer el nombre de la marca en el campo de búsqueda
        if self.instance and self.instance.pk:
            marca = Marca.objects.filter(codigo_marca=self.instance.codigo_marca).first()
            self.initial['marca_search'] = f"{self.instance.codigo_marca} - {marca.nombre_marca}" if marca else str(self.instance.codigo_marca)

    def clean_marca_search(self):
        """Validar y convertir el nombre de marca al código correspondiente"""
        marca_search = self.cleaned_data.get('marca_search')
        if not marca_search:
            raise forms.ValidationError("Debe seleccionar una marca válida.")

        # Intentar extraer el código de la cadena "ID - Nombre"
        try:
            if ' - ' in marca_search:
                codigo_str = marca_search.split(' - ')[0].strip()
                codigo = int(codigo_str)
            else:
                # Si no tiene el formato, buscar por nombre exacto
                marca = Marca.objects.filter(nombre_marca__iexact=marca_search.strip()).first()
                if marca:
                    codigo = marca.codigo_marca
                else:
                    raise forms.ValidationError("Marca no encontrada.")

            # Verificar que la marca existe
            marca = Marca.objects.filter(codigo_marca=codigo).first()
            if not marca:
                raise forms.ValidationError("Marca no encontrada.")

            # Establecer el código en el campo oculto
            self.cleaned_data['codigo_marca'] = str(codigo)
            return marca_search

        except (ValueError, IndexError):
            raise forms.ValidationError("Formato de marca inválido. Use el selector de marcas.")


def relojes_cliente_list(request, cliente_id):
    """
    Vista que lista todos los relojes registrados para un cliente específico.
    
    Muestra los relojes que han pasado por el negocio de ese cliente.
    """
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    relojes = RelojCliente.objects.filter(codigo_cliente=cliente_id)
    return render(request, 'core/relojes_cliente_list.html', {
        'cliente': cliente,
        'relojes': relojes
    })


def relojes_cliente_create(request, cliente_id):
    """
    Vista para crear un nuevo reloj para un cliente específico.
    
    Registra un reloj que pertenece al cliente.
    """
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == 'POST':
        form = RelojClienteForm(request.POST)
        if form.is_valid():
            reloj = form.save(commit=False)
            reloj.codigo_cliente = cliente_id
            reloj.codigo_reloj_cliente = obtener_siguiente_valor('SEQ_RELOJES_CLIENTE')
            reloj.save()
            return redirect('relojes_cliente_list', cliente_id=cliente_id)
    else:
        form = RelojClienteForm()
    marcas = Marca.objects.all()
    return render(request, 'core/relojes_cliente_form.html', {
        'form': form,
        'cliente': cliente,
        'title': 'Crear Reloj del Cliente',
        'marcas': marcas
    })


def relojes_cliente_edit(request, cliente_id, reloj_id):
    """
    Vista para editar un reloj existente de un cliente.
    
    Permite modificar la información de un reloj registrado.
    """
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    reloj = get_object_or_404(RelojCliente, pk=reloj_id, codigo_cliente=cliente_id)
    if request.method == 'POST':
        form = RelojClienteForm(request.POST, instance=reloj)
        if form.is_valid():
            form.save()
            return redirect('relojes_cliente_list', cliente_id=cliente_id)
    else:
        form = RelojClienteForm(instance=reloj)
    marcas = Marca.objects.all()
    return render(request, 'core/relojes_cliente_form.html', {
        'form': form,
        'cliente': cliente,
        'title': 'Editar Reloj del Cliente',
        'marcas': marcas
    })


def relojes_cliente_delete(request, cliente_id, reloj_id):
    """
    Vista para eliminar un reloj de un cliente.
    
    Elimina el registro del reloj del cliente.
    """
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    reloj = get_object_or_404(RelojCliente, pk=reloj_id, codigo_cliente=cliente_id)
    if request.method == 'POST':
        reloj.delete()
        return redirect('relojes_cliente_list', cliente_id=cliente_id)
    return render(request, 'core/relojes_cliente_confirm_delete.html', {
        'cliente': cliente,
        'reloj': reloj
    })


# =========================================================================================
# CRUD: TIPOS DE PRODUCTO (Interfaz Web)
# =========================================================================================

class TipoProductoForm(forms.ModelForm):
    """
    Formulario para crear y editar tipos de productos.
    
    Un tipo de producto es una categoría (Relojes, Repuestos, Servicios, etc.)
    """
    class Meta:
        model = TipoProducto
        fields = ['nombre_tipo_producto']
        widgets = {
            'nombre_tipo_producto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Relojes, Repuestos, Servicios'}),
        }


def tipos_producto_list(request):
    """
    Vista que lista todos los tipos de productos disponibles.
    
    Muestra cuántos productos hay de cada tipo y permite administrarlos.
    """
    tipos = TipoProducto.objects.all()
    return render(request, 'core/tipos_producto_list.html', {'tipos': tipos})


def tipo_producto_create(request):
    """
    Vista para crear un nuevo tipo de producto.
    
    Los tipos de producto son categorías para organizar el inventario.
    """
    if request.method == 'POST':
        form = TipoProductoForm(request.POST)
        if form.is_valid():
            tipo = form.save(commit=False)
            tipo.codigo_tipo_producto = obtener_siguiente_valor('SEQ_TIPO_PRODUCTOS')
            tipo.save()
            return redirect('tipos_producto_list')
    else:
        form = TipoProductoForm()
    return render(request, 'core/tipo_producto_form.html', {'form': form, 'title': 'Crear Tipo de Producto'})


def tipo_producto_edit(request, pk):
    """
    Vista para editar un tipo de producto existente.
    """
    tipo = get_object_or_404(TipoProducto, pk=pk)
    if request.method == 'POST':
        form = TipoProductoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect('tipos_producto_list')
    else:
        form = TipoProductoForm(instance=tipo)
    return render(request, 'core/tipo_producto_form.html', {'form': form, 'title': 'Editar Tipo de Producto'})


def tipo_producto_delete(request, pk):
    """
    Vista para eliminar un tipo de producto.
    
    Muestra confirmación antes de eliminar.
    """
    tipo = get_object_or_404(TipoProducto, pk=pk)
    if request.method == 'POST':
        tipo.delete()
        return redirect('tipos_producto_list')
    return render(request, 'core/tipo_producto_confirm_delete.html', {'tipo': tipo})


# =========================================================================================
# CRUD: PRODUCTOS (Interfaz Web)
# =========================================================================================

class ProductoForm(forms.ModelForm):
    """
    Formulario para crear y editar productos.
    
    Un producto es un artículo vendible: relojes, repuestos, servicios, etc.
    """
    marca_nombre = forms.CharField(
        required=True,
        label='Marca',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe o selecciona una marca',
        })
    )
    codigo_marca = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    tipo_producto_nombre = forms.CharField(
        required=True,
        label='Tipo de Producto',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe o selecciona un tipo de producto',
        })
    )
    codigo_tipo_producto = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    ultima_actualizacion_producto = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'disabled': 'disabled'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo_marca'].required = False
        self.fields['codigo_tipo_producto'].required = False
        if self.instance and self.instance.pk:
            marca = Marca.objects.filter(codigo_marca=self.instance.codigo_marca).first()
            tipo = TipoProducto.objects.filter(codigo_tipo_producto=self.instance.codigo_tipo_producto).first()
            if marca:
                self.initial['marca_nombre'] = marca.nombre_marca
                self.initial['codigo_marca'] = marca.codigo_marca
            if tipo:
                self.initial['tipo_producto_nombre'] = tipo.nombre_tipo_producto
                self.initial['codigo_tipo_producto'] = tipo.codigo_tipo_producto

    def clean_marca_nombre(self):
        nombre = self.cleaned_data.get('marca_nombre')
        if not nombre:
            raise forms.ValidationError('Selecciona una marca válida.')

        marca = Marca.objects.filter(nombre_marca__iexact=nombre).first()
        if not marca:
            raise forms.ValidationError('Marca no válida. Selecciona una marca existente.')

        self.cleaned_data['codigo_marca'] = marca.codigo_marca
        return nombre

    def clean_tipo_producto_nombre(self):
        nombre = self.cleaned_data.get('tipo_producto_nombre')
        if not nombre:
            raise forms.ValidationError('Selecciona un tipo de producto válido.')

        tipo = TipoProducto.objects.filter(nombre_tipo_producto__iexact=nombre).first()
        if not tipo:
            raise forms.ValidationError('Tipo de producto no válido. Selecciona un tipo existente.')

        self.cleaned_data['codigo_tipo_producto'] = tipo.codigo_tipo_producto
        return nombre

    class Meta:
        model = Producto
        fields = ['nombre_producto', 'codigo_marca', 'codigo_tipo_producto',
                 'modelo_producto', 'precio_venta_producto', 'costo_producto', 'garantia_producto',
                 'descripcion_producto', 'stock_disponible_producto', 'stock_minimo_producto',
                 'controla_stock', 'ultima_actualizacion_producto']
        widgets = {
            'nombre_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo_producto': forms.TextInput(attrs={'class': 'form-control'}),
            'precio_venta_producto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'costo_producto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'garantia_producto': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion_producto': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'stock_disponible_producto': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo_producto': forms.NumberInput(attrs={'class': 'form-control'}),
            'controla_stock': forms.Select(attrs={'class': 'form-select'}, choices=[('S', 'Sí'), ('N', 'No')]),
        }


def productos_list(request):
    """
    Vista que lista todos los productos en el inventario.
    
    Muestra información importante:
    - Stock actual vs mínimo (alerta si está bajo)
    - Precios y margen de ganancia
    - Disponibilidad para venta
    """
    productos = Producto.objects.all()
    return render(request, 'core/productos_list.html', {'productos': productos})


def producto_create(request):
    """
    Vista para crear un nuevo producto.
    
    Se requiere:
    - Información básica (nombre, código, modelo)
    - Pricing (costo, precio de venta)
    - Control de inventario (stock inicial, mínimo)
    - Información de garantía y descripción
    """
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.codigo_producto = obtener_siguiente_valor('SEQ_PRODUCTOS')
            producto.ultima_actualizacion_producto = date.today()
            producto.save()
            return redirect('productos_list')
    else:
        form = ProductoForm()
    marcas = Marca.objects.all()
    tipos = TipoProducto.objects.all()
    return render(request, 'core/producto_form.html', {'form': form, 'title': 'Crear Producto', 'marcas': marcas, 'tipos': tipos})


def producto_edit(request, pk):
    """
    Vista para editar un producto existente.
    
    Permite cambiar todos los atributos incluyendo precios e inventario.
    """
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto_actualizado = form.save(commit=False)
            producto_actualizado.ultima_actualizacion_producto = date.today()
            producto_actualizado.save()
            return redirect('productos_list')
    else:
        form = ProductoForm(instance=producto)
    marcas = Marca.objects.all()
    tipos = TipoProducto.objects.all()
    return render(request, 'core/producto_form.html', {'form': form, 'title': 'Editar Producto', 'producto': producto, 'marcas': marcas, 'tipos': tipos})


def producto_delete(request, pk):
    """
    Vista para eliminar un producto del catálogo.
    
    Muestra confirmación antes de eliminar definitivamente.
    """
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        return redirect('productos_list')
    return render(request, 'core/producto_confirm_delete.html', {'producto': producto})


def obtener_siguiente_valor(secuencia):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {secuencia}.NEXTVAL FROM DUAL")
        row = cursor.fetchone()
    return row[0]


# =========================================================================================
# CRUD: MARCAS (Interfaz Web)
# =========================================================================================

class MarcaForm(forms.ModelForm):
    """Formulario para crear y editar marcas de productos"""
    
    class Meta:
        model = Marca
        fields = ['nombre_marca']
        widgets = {
            'nombre_marca': forms.TextInput(attrs={'class': 'form-control'}),
        }

def marcas_list(request):
    """Lista todas las marcas"""
    marcas = Marca.objects.all()
    return render(request, 'core/marcas_list.html', {'marcas': marcas})

def marca_create(request):
    """Crear una nueva marca"""
    if request.method == 'POST':
        form = MarcaForm(request.POST)
        if form.is_valid():
            marca = form.save(commit=False)
            marca.codigo_marca = obtener_siguiente_valor('SEQ_MARCAS')
            marca.save()
            return redirect('marcas_list')
    else:
        form = MarcaForm()
    return render(request, 'core/marca_form.html', {'form': form, 'title': 'Crear Marca'})

def marca_edit(request, pk):
    """Editar una marca existente"""
    marca = get_object_or_404(Marca, pk=pk)
    if request.method == 'POST':
        form = MarcaForm(request.POST, instance=marca)
        if form.is_valid():
            form.save()
            return redirect('marcas_list')
    else:
        form = MarcaForm(instance=marca)
    return render(request, 'core/marca_form.html', {'form': form, 'title': 'Editar Marca', 'marca': marca})

def marca_delete(request, pk):
    """Eliminar una marca"""
    marca = get_object_or_404(Marca, pk=pk)
    if request.method == 'POST':
        marca.delete()
        return redirect('marcas_list')
    return render(request, 'core/marca_confirm_delete.html', {'marca': marca})


# =========================================================================================
# CRUD: MÉTODOS DE PAGO (Interfaz Web)
# =========================================================================================

class MetodoPagoForm(forms.ModelForm):
    """Formulario para crear y editar métodos de pago"""
    
    class Meta:
        model = MetodoPago
        fields = ['nombre_metodo_pago']
        widgets = {
            'nombre_metodo_pago': forms.TextInput(attrs={'class': 'form-control'}),
        }

def metodos_pago_list(request):
    """Lista todos los métodos de pago"""
    metodos = MetodoPago.objects.all()
    return render(request, 'core/metodos_pago_list.html', {'metodos': metodos})

def metodo_pago_create(request):
    """Crear un nuevo método de pago"""
    if request.method == 'POST':
        form = MetodoPagoForm(request.POST)
        if form.is_valid():
            metodo = form.save(commit=False)
            metodo.codigo_metodo_pago = obtener_siguiente_valor('SEQ_METODOS_PAGO')
            metodo.save()
            return redirect('metodos_pago_list')
    else:
        form = MetodoPagoForm()
    return render(request, 'core/metodo_pago_form.html', {'form': form, 'title': 'Crear Método de Pago'})

def metodo_pago_edit(request, pk):
    """Editar un método de pago existente"""
    metodo = get_object_or_404(MetodoPago, pk=pk)
    if request.method == 'POST':
        form = MetodoPagoForm(request.POST, instance=metodo)
        if form.is_valid():
            form.save()
            return redirect('metodos_pago_list')
    else:
        form = MetodoPagoForm(instance=metodo)
    return render(request, 'core/metodo_pago_form.html', {'form': form, 'title': 'Editar Método de Pago', 'metodo': metodo})

def metodo_pago_delete(request, pk):
    """Eliminar un método de pago"""
    metodo = get_object_or_404(MetodoPago, pk=pk)
    if request.method == 'POST':
        metodo.delete()
        return redirect('metodos_pago_list')
    return render(request, 'core/metodo_pago_confirm_delete.html', {'metodo': metodo})


# =========================================================================================
# CRUD: TIPOS DE SERVICIO (Interfaz Web)
# =========================================================================================

class TipoServicioForm(forms.ModelForm):
    """Formulario para crear y editar tipos de servicio"""
    
    class Meta:
        model = TipoServicio
        fields = ['nombre_tipo_servicio']
        widgets = {
            'nombre_tipo_servicio': forms.TextInput(attrs={'class': 'form-control'}),
        }

def tipos_servicio_list(request):
    """Lista todos los tipos de servicio"""
    tipos = TipoServicio.objects.all()
    return render(request, 'core/tipos_servicio_list.html', {'tipos': tipos})

def tipo_servicio_create(request):
    """Crear un nuevo tipo de servicio"""
    if request.method == 'POST':
        form = TipoServicioForm(request.POST)
        if form.is_valid():
            tipo = form.save(commit=False)
            tipo.codigo_tipo_servicio = obtener_siguiente_valor('SEQ_TIPOS_SERVICIO')
            tipo.save()
            return redirect('tipos_servicio_list')
    else:
        form = TipoServicioForm()
    return render(request, 'core/tipo_servicio_form.html', {'form': form, 'title': 'Crear Tipo de Servicio'})

def tipo_servicio_edit(request, pk):
    """Editar un tipo de servicio existente"""
    tipo = get_object_or_404(TipoServicio, pk=pk)
    if request.method == 'POST':
        form = TipoServicioForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect('tipos_servicio_list')
    else:
        form = TipoServicioForm(instance=tipo)
    return render(request, 'core/tipo_servicio_form.html', {'form': form, 'title': 'Editar Tipo de Servicio', 'tipo': tipo})

def tipo_servicio_delete(request, pk):
    """Eliminar un tipo de servicio"""
    tipo = get_object_or_404(TipoServicio, pk=pk)
    if request.method == 'POST':
        tipo.delete()
        return redirect('tipos_servicio_list')
    return render(request, 'core/tipo_servicio_confirm_delete.html', {'tipo': tipo})


# =========================================================================================
# CRUD: ESTADOS DE SERVICIO (Interfaz Web)
# =========================================================================================

class EstadoServicioForm(forms.ModelForm):
    """Formulario para crear y editar estados de servicio"""
    
    class Meta:
        model = EstadoServicio
        fields = ['nombre_estado_reparacion']
        widgets = {
            'nombre_estado_reparacion': forms.TextInput(attrs={'class': 'form-control'}),
        }

def estados_servicio_list(request):
    """Lista todos los estados de servicio"""
    estados = EstadoServicio.objects.all()
    return render(request, 'core/estados_servicio_list.html', {'estados': estados})

def estado_servicio_create(request):
    """Crear un nuevo estado de servicio"""
    if request.method == 'POST':
        form = EstadoServicioForm(request.POST)
        if form.is_valid():
            estado = form.save(commit=False)
            estado.codigo_estado_servicio = obtener_siguiente_valor('SEQ_ESTADOS_SERVICIO')
            estado.save()
            return redirect('estados_servicio_list')
    else:
        form = EstadoServicioForm()
    return render(request, 'core/estado_servicio_form.html', {'form': form, 'title': 'Crear Estado de Servicio'})

def estado_servicio_edit(request, pk):
    """Editar un estado de servicio existente"""
    estado = get_object_or_404(EstadoServicio, pk=pk)
    if request.method == 'POST':
        form = EstadoServicioForm(request.POST, instance=estado)
        if form.is_valid():
            form.save()
            return redirect('estados_servicio_list')
    else:
        form = EstadoServicioForm(instance=estado)
    return render(request, 'core/estado_servicio_form.html', {'form': form, 'title': 'Editar Estado de Servicio', 'estado': estado})

def estado_servicio_delete(request, pk):
    """Eliminar un estado de servicio"""
    estado = get_object_or_404(EstadoServicio, pk=pk)
    if request.method == 'POST':
        estado.delete()
        return redirect('estados_servicio_list')
    return render(request, 'core/estado_servicio_confirm_delete.html', {'estado': estado})


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
@permission_classes([AllowAny])
@authentication_classes([])
def login_empleado(request):
    correo = request.data.get('correo')
    contrasena = request.data.get('contrasena')

    if not correo or not contrasena:
        return Response(
            {
                "error": "Correo y contraseña son obligatorios"
            }, status= 400
        )

    try:
        empleado = Empleado.objects.get(correo_empleado = correo)

        if not check_password(contrasena, empleado.password):
            return Response(
                {
                    "error": "Credenciales invalidas"
                }, status= 401
            )
        
        # Generar Token Manual
        refresh = RefreshToken.for_user(empleado)

        refresh['perfil'] = empleado.codigo_perfil_empleado

        # Validar Contraseña
        return Response({
            "mensaje": "Login Exitoso",
            "empleado": {
                "id": empleado.identificacion_empleado,
                "nombre": empleado.nombre_empleado,
                "primer_apellido": empleado.primer_apellido_empleado,
                "correo": empleado.correo_empleado,
                "perfil": empleado.codigo_perfil_empleado
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })

    except Empleado.DoesNotExist:
        return Response(
            {
                "error": "Usuario no encontrado"
            }, status= 404
        )

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
    

@api_view(['GET'])
def listar_ventas(request):
    try:
        ventas = Venta.objects.all()

        data = []

        for venta in ventas:
            data.append(
                {
                    "codigo_venta": venta.codigo_venta,
                    "cliente": venta.identificacion_cliente_venta,
                    "empleado": venta.identificacion_empleado_venta,
                    "total": venta.total_venta,
                    "fecha": venta.fecha_venta,
                    "metodo_pago": venta.codigo_metodo_pago
                }
            )

        return Response(data)
    
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
    

@api_view(['GET'])
def listar_productos(request):
    try:
        productos = Producto.objects.all()

        data = []

        for p in productos:
            data.append(
                {
                    "codigo": p.codigo_producto,
                    "nombre": p.nombre_producto,
                    "marca": p.codigo_marca,
                    "tipo_producto": p.codigo_tipo_producto,
                    "modelo": p.modelo_producto,
                    "precio_venta": p.precio_venta_producto,
                    "costo": p.costo_producto,
                    "descripcion": p.descripcion_producto,
                    "garantia_meses": p.garantia_producto,
                    "stock_disponible": p.stock_disponible_producto,
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
def obtener_producto(request, codigo):
    try:
        producto = Producto.objects.get(codigo_producto=codigo)

        data = {
            "codigo": producto.codigo_producto,
            "nombre": producto.nombre_producto,
            "marca": producto.codigo_marca,
            "tipo_producto": producto.codigo_tipo_producto,
            "modelo": producto.modelo_producto,
            "precio_venta": producto.precio_venta_producto,
            "costo": producto.costo_producto,
            "descripcion": producto.descripcion_producto,
            "garantia_meses": producto.garantia_producto,
            "stock_disponible": producto.stock_disponible_producto,
        }

        return Response(data)

    except Producto.DoesNotExist:
        return Response(
            {
                "error": "Producto no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )

@api_view(['POST'])
def crear_producto(request):
    try:
        nombre = request.data.get('nombre')
        marca = request.data.get('marca')
        tipo_producto = request.data.get('tipo_producto')
        modelo = request.data.get('modelo')
        precio_venta = request.data.get('precio_venta')
        costo = request.data.get('costo')
        garantia_meses = request.data.get('garantia_meses')
        descripcion = request.data.get('descripcion')
        stock_disponible = request.data.get('stock_disponible')
        stock_minimo = request.data.get('stock_minimo')
        controla_stock = request.data.get('controla_stock')
        ultima_actualizacion_producto = datetime.now()

        # Validaciones de campos obligatorios
        if not nombre:
            return Response(
                {
                    "error": "El campo 'nombre' es obligatorio"
                }, status=400
            )
        
        if not marca:
            return Response(
                {
                    "error": "El campo 'marca' es obligatorio"
                }, status=400
            )
        
        if not tipo_producto:
            return Response(
                {
                    "error": "El campo 'tipo_producto' es obligatorio"
                }, status=400
            )
        
        if not modelo:
            return Response(
                {
                    "error": "El campo 'modelo' es obligatorio"
                }, status=400
            )
        
        if precio_venta is None:
            return Response(
                {
                    "error": "El campo 'precio_venta' es obligatorio"
                }, status=400
            )
        
        if costo is None:
            return Response(
                {
                    "error": "El campo 'costo' es obligatorio"
                }, status=400
            )
        
        if controla_stock not in ['S', 'N']:
            return Response(
                {
                    "error": "El campo 'controla_stock' debe ser 'S' o 'N'"
                }, status=400
            )
        
        if controla_stock == 'S' and stock_disponible is None:
            return Response(
                {
                    "error": "El campo 'stock_disponible' es obligatorio cuando controla_stock es 'S'"
                }, status=400
            )
        
        if stock_minimo is not None and (not isinstance(stock_minimo, int) or stock_minimo < 0):
            return Response(
                {
                    "error": "El campo 'stock_minimo' debe ser un entero positivo"
                }, status=400
            )
        
        producto_id = obtener_siguiente_valor('SEQ_PRODUCTOS')

        producto = Producto(
            codigo_producto = producto_id,
            nombre_producto = nombre,
            codigo_marca = marca,
            codigo_tipo_producto = tipo_producto,
            modelo_producto = modelo,
            precio_venta_producto = precio_venta,
            costo_producto = costo,
            descripcion_producto = descripcion,
            garantia_producto = garantia_meses,
            controla_stock = controla_stock,
            stock_disponible_producto = stock_disponible,
            stock_minimo_producto = stock_minimo,
            ultima_actualizacion_producto = ultima_actualizacion_producto
        )

        producto.save()

        return Response(
            {
                "mensaje": "Producto creado correctamente",
                "codigo": producto_id
            }
        )

    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['PUT'])
def actualizar_producto(request, codigo):
    try:
        producto = Producto.objects.get(codigo_producto=codigo)

        nombre = request.data.get('nombre')
        marca = request.data.get('marca')
        tipo_producto = request.data.get('tipo_producto')
        modelo = request.data.get('modelo')
        precio_venta = request.data.get('precio_venta')
        costo = request.data.get('costo')
        garantia_meses = request.data.get('garantia_meses')
        descripcion = request.data.get('descripcion')
        stock_disponible = request.data.get('stock_disponible')
        stock_minimo = request.data.get('stock_minimo')
        controla_stock = request.data.get('controla_stock')

        if nombre:
            producto.nombre_producto = nombre
        
        if marca:
            producto.codigo_marca = marca
        
        if tipo_producto:
            producto.codigo_tipo_producto = tipo_producto
        
        if modelo:
            producto.modelo_producto = modelo
        
        if precio_venta is not None:
            producto.precio_venta_producto = precio_venta
        
        if costo is not None:
            producto.costo_producto = costo
        
        if garantia_meses is not None:
            producto.garantia_producto = garantia_meses
        
        if descripcion:
            producto.descripcion_producto = descripcion
        
        if controla_stock in ['S', 'N']:
            producto.controla_stock = controla_stock
        
        if stock_disponible is not None:
            producto.stock_disponible_producto = stock_disponible
        
        if stock_minimo is not None:
            producto.stock_minimo_producto = stock_minimo

        producto.save()

        return Response(
            {
                "mensaje": "Producto actualizado correctamente"
            }
        )

    except Producto.DoesNotExist:
        return Response(
            {
                "error": "Producto no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['DELETE'])
def eliminar_producto(request, codigo):
    try:
        producto = Producto.objects.get(codigo_producto=codigo)
        producto.delete()

        return Response(
            {
                "mensaje": "Producto eliminado correctamente"
            }
        )

    except Producto.DoesNotExist:
        return Response(
            {
                "error": "Producto no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )


@api_view(['GET'])
def listar_tipos_producto(request):
    try:
        tipos = TipoProducto.objects.all()

        data = []

        for t in tipos:
            data.append(
                {
                    "codigo": t.codigo_tipo_producto,
                    "nombre": t.nombre_tipo_producto
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
def obtener_tipo_producto(request, codigo):
    try:
        tipo = TipoProducto.objects.get(codigo_tipo_producto=codigo)

        data = {
            "codigo": tipo.codigo_tipo_producto,
            "nombre": tipo.nombre_tipo_producto
        }

        return Response(data)

    except TipoProducto.DoesNotExist:
        return Response(
            {
                "error": "Tipo de producto no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['POST'])
def crear_tipo_producto(request):
    try:
        nombre = request.data.get('nombre')

        if not nombre:
            return Response(
                {
                    "error": "El campo 'nombre' es obligatorio"
                }, status=400
            )
        
        if len(nombre) > 40:
            return Response(
                {
                    "error": "El nombre es demasiado largo"
                }, status=400
            )
        
        codigo = obtener_siguiente_valor('SEQ_TIPO_PRODUCTOS')

        tipo = TipoProducto(
            codigo_tipo_producto = codigo,
            nombre_tipo_producto = nombre
        )

        tipo.save()

        return Response(
            {
                "mensaje": "Tipo de producto creado correctamente",
                "codigo": codigo
            }
        )

    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )

@api_view(['PUT'])
def actualizar_tipo_producto(request, codigo):
    try:
        tipo = TipoProducto.objects.get(codigo_tipo_producto=codigo)

        nombre = request.data.get('nombre')

        if nombre:
            if len(nombre) > 40:
                return Response(
                    {
                        "error": "El nombre es demasiado largo"
                    }, status=400
                )
            tipo.nombre_tipo_producto = nombre
            tipo.save()

        return Response(
            {
                "mensaje": "Tipo de producto actualizado correctamente"
            }
        )

    except TipoProducto.DoesNotExist:
        return Response(
            {
                "error": "Tipo de producto no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['DELETE'])
def eliminar_tipo_producto(request, codigo):
    try:
        tipo = TipoProducto.objects.get(codigo_tipo_producto=codigo)
        tipo.delete()

        return Response(
            {
                "mensaje": "Tipo de producto eliminado correctamente"
            }
        )

    except TipoProducto.DoesNotExist:
        return Response(
            {
                "error": "Tipo de producto no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['GET'])
def listar_marcas(request):
    try:
        marcas = Marca.objects.all()

        data = []

        for m in marcas:
            data.append(
                {
                    "codigo": m.codigo_marca,
                    "nombre": m.nombre_marca
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
def obtener_marca(request, codigo):
    try:
        marca = Marca.objects.get(codigo_marca=codigo)

        data = {
            "codigo": marca.codigo_marca,
            "nombre": marca.nombre_marca
        }

        return Response(data)

    except Marca.DoesNotExist:
        return Response(
            {
                "error": "Marca no encontrada"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['POST'])
def crear_marca(request):
    try:
        nombre = request.data.get('nombre')

        if not nombre:
            return Response(
                {
                    "error": "El campo 'nombre' es obligatorio"
                }, status=400
            )
        
        if len(nombre) > 40:
            return Response(
                {
                    "error": "El nombre es demasiado largo"
                }, status=400
            )
        
        codigo = obtener_siguiente_valor('SEQ_MARCAS')

        marca = Marca(
            codigo_marca = codigo,
            nombre_marca = nombre
        )

        marca.save()

        return Response(
            {
                "mensaje": "Marca creada correctamente",
                "codigo": codigo
            }
        )

    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['PUT'])
def actualizar_marca(request, codigo):
    try:
        marca = Marca.objects.get(codigo_marca=codigo)

        nombre = request.data.get('nombre')

        if nombre:
            if len(nombre) > 40:
                return Response(
                    {
                        "error": "El nombre es demasiado largo"
                    }, status=400
                )
            marca.nombre_marca = nombre
            marca.save()

        return Response(
            {
                "mensaje": "Marca actualizada correctamente"
            }
        )

    except Marca.DoesNotExist:
        return Response(
            {
                "error": "Marca no encontrada"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['DELETE'])
def eliminar_marca(request, codigo):
    try:
        marca = Marca.objects.get(codigo_marca=codigo)
        marca.delete()

        return Response(
            {
                "mensaje": "Marca eliminada correctamente"
            }
        )

    except Marca.DoesNotExist:
        return Response(
            {
                "error": "Marca no encontrada"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    

@api_view(['GET'])
def listar_estados_servicio(request):
    try:
        estados = EstadoServicio.objects.all()

        data = []

        for e in estados:
            data.append(
                {
                    "codigo": e.codigo_estado_servicio,
                    "nombre": e.nombre_estado_reparacion
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
def obtener_estado_servicio(request, codigo):
    try:
        estado = EstadoServicio.objects.get(codigo_estado_servicio=codigo)

        data = {
            "codigo": estado.codigo_estado_servicio,
            "nombre": estado.nombre_estado_reparacion
        }

        return Response(data)

    except EstadoServicio.DoesNotExist:
        return Response(
            {
                "error": "Estado de servicio no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['POST'])
def crear_estado_servicio(request):
    try:
        nombre = request.data.get('nombre')

        if not nombre:
            return Response(
                {
                    "error": "El campo 'nombre' es obligatorio"
                }, status=400
            )
        
        if len(nombre) > 20:
            return Response(
                {
                    "error": "El nombre es demasiado largo"
                }, status=400
            )
        
        codigo = obtener_siguiente_valor('SEQ_ESTADOS_SERVICIO')

        estado = EstadoServicio(
            codigo_estado_servicio = codigo,
            nombre_estado_reparacion = nombre
        )

        estado.save()

        return Response(
            {
                "mensaje": "Estado de servicio creado correctamente",
                "codigo": codigo
            }
        )

    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['PUT'])
def actualizar_estado_servicio(request, codigo):
    try:
        estado = EstadoServicio.objects.get(codigo_estado_servicio=codigo)

        nombre = request.data.get('nombre')

        if nombre:
            if len(nombre) > 20:
                return Response(
                    {
                        "error": "El nombre es demasiado largo"
                    }, status=400
                )
            estado.nombre_estado_reparacion = nombre
            estado.save()

        return Response(
            {
                "mensaje": "Estado de servicio actualizado correctamente"
            }
        )

    except EstadoServicio.DoesNotExist:
        return Response(
            {
                "error": "Estado de servicio no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['DELETE'])
def eliminar_estado_servicio(request, codigo):
    try:
        estado = EstadoServicio.objects.get(codigo_estado_servicio=codigo)
        estado.delete()

        return Response(
            {
                "mensaje": "Estado de servicio eliminado correctamente"
            }
        )

    except EstadoServicio.DoesNotExist:
        return Response(
            {
                "error": "Estado de servicio no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    

@api_view(['GET'])
def listar_tipos_servicio(request):
    try:
        tipos = TipoServicio.objects.all()

        data = []

        for t in tipos:
            data.append(
                {
                    "codigo": t.codigo_tipo_servicio,
                    "nombre": t.nombre_tipo_servicio
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
def obtener_tipo_servicio(request, codigo):
    try:
        tipo = TipoServicio.objects.get(codigo_tipo_servicio=codigo)

        data = {
            "codigo": tipo.codigo_tipo_servicio,
            "nombre": tipo.nombre_tipo_servicio
        }

        return Response(data)

    except TipoServicio.DoesNotExist:
        return Response(
            {
                "error": "Tipo de servicio no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['POST'])
def crear_tipo_servicio(request):
    try:
        nombre = request.data.get('nombre')

        if not nombre:
            return Response(
                {
                    "error": "El campo 'nombre' es obligatorio"
                }, status=400
            )
        
        if len(nombre) > 40:
            return Response(
                {
                    "error": "El nombre es demasiado largo"
                }, status=400
            )
        
        codigo = obtener_siguiente_valor('SEQ_TIPOS_SERVICIO')

        tipo = TipoServicio(
            codigo_tipo_servicio = codigo,
            nombre_tipo_servicio = nombre
        )

        tipo.save()

        return Response(
            {
                "mensaje": "Tipo de servicio creado correctamente",
                "codigo": codigo
            }
        )

    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['PUT'])
def actualizar_tipo_servicio(request, codigo):
    try:
        tipo = TipoServicio.objects.get(codigo_tipo_servicio=codigo)

        nombre = request.data.get('nombre')

        if nombre:
            if len(nombre) > 40:
                return Response(
                    {
                        "error": "El nombre es demasiado largo"
                    }, status=400
                )
            tipo.nombre_tipo_servicio = nombre
            tipo.save()

        return Response(
            {
                "mensaje": "Tipo de servicio actualizado correctamente"
            }
        )

    except TipoServicio.DoesNotExist:
        return Response(
            {
                "error": "Tipo de servicio no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['DELETE'])
def eliminar_tipo_servicio(request, codigo):
    try:
        tipo = TipoServicio.objects.get(codigo_tipo_servicio=codigo)
        tipo.delete()

        return Response(
            {
                "mensaje": "Tipo de servicio eliminado correctamente"
            }
        )

    except TipoServicio.DoesNotExist:
        return Response(
            {
                "error": "Tipo de servicio no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    

@api_view(['GET'])
def listar_relojes_todos_clientes(request):
    try:
        relojes = RelojCliente.objects.all()

        data = []

        for r in relojes:
            data.append(
                {
                    "codigo_reloj": r.codigo_reloj_cliente,
                    "codigo_cliente": r.codigo_cliente,
                    "marca": r.codigo_marca,
                    "modelo": r.modelo,
                    "descripcion": r.descripcion_reloj
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
def listar_relojes_cliente(request, cliente_id):
    try:
        relojes = RelojCliente.objects.filter(codigo_cliente=cliente_id)

        data = []

        for r in relojes:
            data.append(
                {
                    "codigo_reloj": r.codigo_reloj_cliente,
                    "codigo_cliente": r.codigo_cliente,
                    "marca": r.codigo_marca,
                    "modelo": r.modelo,
                    "descripcion": r.descripcion_reloj
                }
            )

        return Response(data)

    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['POST'])
def crear_reloj_cliente(request):
    try:
        cliente_id = request.data.get('cliente_id')
        marca = request.data.get('marca')
        modelo = request.data.get('modelo')
        descripcion = request.data.get('descripcion')

        if not cliente_id:
            return Response(
                {
                    "error": "El campo 'cliente_id' es obligatorio"
                }, status=400
            )
        
        if not marca:
            return Response(
                {
                    "error": "El campo 'marca' es obligatorio"
                }, status=400
            )
        
        if not modelo:
            return Response(
                {
                    "error": "El campo 'modelo' es obligatorio"
                }, status=400
            )
        
        codigo_reloj = obtener_siguiente_valor('SEQ_RELOJES_CLIENTE')

        reloj = RelojCliente(
            codigo_reloj_cliente = codigo_reloj,
            codigo_cliente = cliente_id,
            codigo_marca = marca,
            modelo = modelo,
            descripcion_reloj = descripcion
        )

        reloj.save()

        return Response(
            {
                "codigo_reloj": codigo_reloj,
                "mensaje": "Reloj del cliente creado correctamente",
                "codigo_cliente": cliente_id,
                "modelo": modelo,
                "descripcion": descripcion
            }
        )

    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    

@api_view(['GET'])
def listar_metodos_pago(request):
    try:
        metodos = MetodoPago.objects.all()

        data = []

        for m in metodos:
            data.append(
                {
                    "codigo": m.codigo_metodo_pago,
                    "nombre": m.nombre_metodo_pago
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
def obtener_metodo_pago(request, codigo):
    try:
        metodo = MetodoPago.objects.get(codigo_metodo_pago=codigo)

        data = {
            "codigo": metodo.codigo_metodo_pago,
            "nombre": metodo.nombre_metodo_pago
        }

        return Response(data)

    except MetodoPago.DoesNotExist:
        return Response(
            {
                "error": "Método de pago no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['POST'])
def crear_metodo_pago(request):
    try:
        nombre = request.data.get('nombre')

        if not nombre:
            return Response(
                {
                    "error": "El campo 'nombre' es obligatorio"
                }, status=400
            )
        
        if len(nombre) > 30:
            return Response(
                {
                    "error": "El nombre es demasiado largo"
                }, status=400
            )
        
        codigo = obtener_siguiente_valor('SEQ_METODOS_PAGO')

        metodo = MetodoPago(
            codigo_metodo_pago = codigo,
            nombre_metodo_pago = nombre
        )

        metodo.save()

        return Response(
            {
                "mensaje": "Método de pago creado correctamente",
                "codigo": codigo
            }
        )

    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['PUT'])
def actualizar_metodo_pago(request, codigo):
    try:
        metodo = MetodoPago.objects.get(codigo_metodo_pago=codigo)

        nombre = request.data.get('nombre')

        if nombre:
            if len(nombre) > 30:
                return Response(
                    {
                        "error": "El nombre es demasiado largo"
                    }, status=400
                )
            metodo.nombre_metodo_pago = nombre
            metodo.save()

        return Response(
            {
                "mensaje": "Método de pago actualizado correctamente"
            }
        )

    except MetodoPago.DoesNotExist:
        return Response(
            {
                "error": "Método de pago no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )
    
@api_view(['DELETE'])
def eliminar_metodo_pago(request, codigo):
    try:
        metodo = MetodoPago.objects.get(codigo_metodo_pago=codigo)
        metodo.delete()

        return Response(
            {
                "mensaje": "Método de pago eliminado correctamente"
            }
        )

    except MetodoPago.DoesNotExist:
        return Response(
            {
                "error": "Método de pago no encontrado"
            }, status=404
        )
    
    except Exception as e:
        return Response(
            {
                "error": str(e)
            }, status=400
        )


# =========================
# SERVICIOS
# =========================

@api_view(['GET'])
def listar_servicios(request):
    try:
        # 🔎 Parámetros de filtro
        codigo_tecnico = request.query_params.get('codigo_tecnico')
        codigo_estado = request.query_params.get('codigo_estado')
        codigo_reloj = request.query_params.get('codigo_reloj')

        # 📦 Query base (TODOS los servicios)
        servicios = Servicio.objects.all()

        # 🔍 FILTROS DINÁMICOS
        if codigo_tecnico:
            servicios = servicios.filter(codigo_tecnico=codigo_tecnico)

        if codigo_estado:
            servicios = servicios.filter(codigo_estado_servicio=codigo_estado)

        if codigo_reloj:
            servicios = servicios.filter(codigo_reloj_cliente=codigo_reloj)

        # 🔽 ORDENAMIENTO
        servicios = servicios.order_by('-codigo_servicio')

        # 📊 SERIALIZACIÓN MANUAL
        data = []

        for servicio in servicios:
            data.append({
                "codigo_servicio": servicio.codigo_servicio,
                "codigo_tecnico": servicio.codigo_tecnico,
                "codigo_tipo_servicio": servicio.codigo_tipo_servicio,
                "codigo_estado_servicio": servicio.codigo_estado_servicio,
                "codigo_detalle_venta": servicio.codigo_detalle_venta,
                "codigo_reloj_cliente": servicio.codigo_reloj_cliente,
                "fecha_servicio": servicio.fecha_servicio,
                "descripcion_falla": servicio.descripcion_falla
            })

        return Response(data)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=400)


@api_view(['GET'])
def obtener_servicio(request, codigo):
    try:
        servicio = Servicio.objects.get(codigo_servicio=codigo)

        data = {
            "codigo_servicio": servicio.codigo_servicio,
            "codigo_tecnico": servicio.codigo_tecnico,
            "codigo_tipo_servicio": servicio.codigo_tipo_servicio,
            "codigo_estado_servicio": servicio.codigo_estado_servicio,
            "codigo_detalle_venta": servicio.codigo_detalle_venta,
            "codigo_reloj_cliente": servicio.codigo_reloj_cliente,
            "fecha_servicio": servicio.fecha_servicio,
            "descripcion_falla": servicio.descripcion_falla
        }

        return Response(data)

    except Servicio.DoesNotExist:
        return Response({
            "error": "Servicio no encontrado"
        }, status=404)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=400)


@api_view(['POST'])
def crear_servicio(request):
    try:
        # Campos obligatorios
        campos_obligatorios = [
            'codigo_tecnico',
            'codigo_tipo_servicio',
            'codigo_estado_servicio',
            'codigo_reloj_cliente',
            # 'fecha_servicio',
            'descripcion_falla'
        ]

        for campo in campos_obligatorios:
            if not request.data.get(campo):
                return Response({
                    "error": f"El campo '{campo}' es obligatorio"
                }, status=400)

        # Validar longitud de descripción
        descripcion = request.data.get('descripcion_falla')
        if len(descripcion) > 500:
            return Response({
                "error": "La descripción de falla es demasiado larga (máximo 500 caracteres)"
            }, status=400)

        # Validar que el técnico (empleado) exista
        codigo_tecnico = request.data.get('codigo_tecnico')
        if not Empleado.objects.filter(identificacion_empleado=codigo_tecnico).exists():
            return Response({
                "error": "El técnico (empleado) no existe"
            }, status=400)

        # Validar que el reloj del cliente exista
        codigo_reloj = request.data.get('codigo_reloj_cliente')
        if not RelojCliente.objects.filter(codigo_reloj_cliente=codigo_reloj).exists():
            return Response({
                "error": "El reloj del cliente no existe"
            }, status=400)

        # Validar que el tipo de servicio exista
        codigo_tipo = request.data.get('codigo_tipo_servicio')
        if not TipoServicio.objects.filter(codigo_tipo_servicio=codigo_tipo).exists():
            return Response({
                "error": "El tipo de servicio no existe"
            }, status=400)

        # Validar que el estado de servicio exista
        codigo_estado = request.data.get('codigo_estado_servicio')
        if not EstadoServicio.objects.filter(codigo_estado_servicio=codigo_estado).exists():
            return Response({
                "error": "El estado de servicio no existe"
            }, status=400)

        # Validar que el detalle de venta existe (si se proporciona)
        codigo_detalle_venta = request.data.get('codigo_detalle_venta')
        if codigo_detalle_venta and not DetalleVenta.objects.filter(codigo_detalle_venta=codigo_detalle_venta).exists():
            return Response({
                "error": "El detalle de venta no existe"
            }, status=400)

        # Obtener el siguiente código de servicio
        codigo_servicio = obtener_siguiente_valor('SEQ_SERVICIOS')

        # Crear el servicio
        servicio = Servicio(
            codigo_servicio=codigo_servicio,
            codigo_tecnico=codigo_tecnico,
            codigo_tipo_servicio=codigo_tipo,
            codigo_estado_servicio=codigo_estado,
            codigo_detalle_venta=codigo_detalle_venta,
            codigo_reloj_cliente=codigo_reloj,
            fecha_servicio=datetime.now(),
            descripcion_falla=descripcion
        )

        servicio.save()

        return Response({
            "mensaje": "Servicio creado correctamente",
            "codigo_servicio": codigo_servicio
        }, status=201)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=400)


@api_view(['PUT'])
def actualizar_servicio(request, codigo):
    try:
        servicio = Servicio.objects.get(codigo_servicio=codigo)

        # Actualizar campos opcionales
        if request.data.get('codigo_tipo_servicio'):
            codigo_tipo = request.data.get('codigo_tipo_servicio')
            if not TipoServicio.objects.filter(codigo_tipo_servicio=codigo_tipo).exists():
                return Response({
                    "error": "El tipo de servicio no existe"
                }, status=400)
            servicio.codigo_tipo_servicio = codigo_tipo

        if request.data.get('codigo_estado_servicio'):
            codigo_estado = request.data.get('codigo_estado_servicio')
            if not EstadoServicio.objects.filter(codigo_estado_servicio=codigo_estado).exists():
                return Response({
                    "error": "El estado de servicio no existe"
                }, status=400)
            servicio.codigo_estado_servicio = codigo_estado

        if request.data.get('descripcion_falla'):
            descripcion = request.data.get('descripcion_falla')
            if len(descripcion) > 500:
                return Response({
                    "error": "La descripción de falla es demasiado larga (máximo 500 caracteres)"
                }, status=400)
            servicio.descripcion_falla = descripcion

        if request.data.get('fecha_servicio'):
            servicio.fecha_servicio = request.data.get('fecha_servicio')

        if request.data.get('codigo_detalle_venta'):
            codigo_detalle = request.data.get('codigo_detalle_venta')
            if not DetalleVenta.objects.filter(codigo_detalle_venta=codigo_detalle).exists():
                return Response({
                    "error": "El detalle de venta no existe"
                }, status=400)
            servicio.codigo_detalle_venta = codigo_detalle

        servicio.save()

        return Response({
            "mensaje": "Servicio actualizado correctamente"
        })

    except Servicio.DoesNotExist:
        return Response({
            "error": "Servicio no encontrado"
        }, status=404)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=400)


@api_view(['DELETE'])
def eliminar_servicio(request, codigo):
    try:
        servicio = Servicio.objects.get(codigo_servicio=codigo)
        servicio.delete()

        return Response({
            "mensaje": "Servicio eliminado correctamente"
        })

    except Servicio.DoesNotExist:
        return Response({
            "error": "Servicio no encontrado"
        }, status=404)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=400)