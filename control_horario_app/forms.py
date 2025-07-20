# control_horario_app/forms.py

from django import forms
from .models import TimeEntry, TimeEntryModificationRequest
from django.utils import timezone
import pytz
from datetime import datetime # Asegúrate de importar datetime
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm # Importar formularios de Django
from django.contrib.auth.models import User # Importar el modelo User
#import datetime

# NUEVOS FORMULARIOS PARA GESTIÓN DE PERFIL
class UserProfileEditForm(UserChangeForm):
    password = None # Elimina el campo de contraseña, ya que se manejará por separado
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name') # Campos que el usuario puede editar

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'username':
                self.fields[field_name].label = "Nombre de Usuario"
            elif field_name == 'email':
                self.fields[field_name].label = "Correo Electrónico"
            elif field_name == 'first_name':
                self.fields[field_name].label = "Nombre"
            elif field_name == 'last_name':
                self.fields[field_name].label = "Apellidos"

class PasswordChangingForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'old_password':
                self.fields[field_name].label = "Contraseña Actual"
            elif field_name == 'new_password1':
                self.fields[field_name].label = "Nueva Contraseña"
            elif field_name == 'new_password2':
                self.fields[field_name].label = "Confirmar Nueva Contraseña"




# --- CLASE BASE DE FORMULARIO PARA LA LÓGICA DE COMBINACIÓN DE FECHAS/HORAS ---
class TimeEntryBaseFormLogic(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Fecha Inicio",
        required=True
    )
    start_time_part = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Hora Inicio",
        required=True
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Fecha Fin",
        required=False
    )
    end_time_part = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Hora Fin",
        required=False
    )

    break_start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Fecha Inicio Descanso",
        required=False
    )
    break_start_time_part = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Hora Inicio Descanso",
        required=False
    )

    break_end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Fecha Fin Descanso",
        required=False
    )
    break_end_time_part = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label="Hora Fin Descanso",
        required=False
    )

    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label="Razón del Cambio",
        required=False,
        help_text="Explica brevemente el motivo de esta modificación o solicitud."
    )

    def clean(self):
        cleaned_data = super().clean()
        
        # --- AÑADE ESTAS LÍNEAS AL PRINCIPIO DEL MÉTODO clean() ---
        print("\n--- DEBUG (forms.py - clean): INICIO ---")
        print(f"DEBUG (forms.py - clean): Raw POST data (parcial): {self.data.dict()}") # Muestra todos los datos enviados
        print(f"DEBUG (forms.py - clean): Datos procesados antes de combinar: {cleaned_data}")
        # --------------------------------------------------------

        # Obtener los datos individuales de forma segura
        start_date = cleaned_data.get('start_date')
        # ... (el resto de tu código de clean) ...

        # --- AÑADE ESTAS LÍNEAS JUSTO ANTES DE 'return cleaned_data' en el método clean() ---
        print(f"DEBUG (forms.py - clean): Datos procesados finales: {cleaned_data}")
        print(f"DEBUG (forms.py - clean): Errores del formulario: {self.errors}")
        print("--- DEBUG (forms.py - clean): FIN ---\n")
        # ----------------------------------------------------------------------------------

        # Obtener los datos individuales de forma segura
        start_date = cleaned_data.get('start_date')
        start_time_part = cleaned_data.get('start_time_part')
        end_date = cleaned_data.get('end_date')
        end_time_part = cleaned_data.get('end_time_part')
        break_start_date = cleaned_data.get('break_start_date')
        break_start_time_part = cleaned_data.get('break_start_time_part')
        break_end_date = cleaned_data.get('break_end_date')
        break_end_time_part = cleaned_data.get('break_end_time_part')

        # Procesar start_time (obligatorio)
        if start_date and start_time_part:
            # Usar datetime.combine con los tipos correctos
            cleaned_data['combined_start_time'] = timezone.make_aware(datetime.combine(start_date, start_time_part))
        else:
            if 'start_date' not in self._errors: self.add_error('start_date', 'La fecha de inicio es obligatoria.')
            if 'start_time_part' not in self._errors: self.add_error('start_time_part', 'La hora de inicio es obligatoria.')
            cleaned_data['combined_start_time'] = None

        # Procesar end_time (opcional)
        if end_date and end_time_part:
            cleaned_data['combined_end_time'] = timezone.make_aware(datetime.combine(end_date, end_time_part))
        elif end_date or end_time_part:
            if 'end_date' not in self._errors: self.add_error('end_date', 'Se requiere tanto la fecha como la hora de fin.')
            if 'end_time_part' not in self._errors: self.add_error('end_time_part', 'Se requiere tanto la fecha como la hora de fin.')
            cleaned_data['combined_end_time'] = None
        else:
            cleaned_data['combined_end_time'] = None

        # Procesar break_start (opcional)
        if break_start_date and break_start_time_part:
            cleaned_data['combined_break_start'] = timezone.make_aware(datetime.combine(break_start_date, break_start_time_part))
        elif break_start_date or break_start_time_part:
            if 'break_start_date' not in self._errors: self.add_error('break_start_date', 'Se requiere tanto la fecha como la hora de inicio de descanso.')
            if 'break_start_time_part' not in self._errors: self.add_error('break_start_time_part', 'Se requiere tanto la fecha como la hora de inicio de descanso.')
            cleaned_data['combined_break_start'] = None
        else:
            cleaned_data['combined_break_start'] = None

        # Procesar break_end (opcional)
        if break_end_date and break_end_time_part:
            cleaned_data['combined_break_end'] = timezone.make_aware(datetime.combine(break_end_date, break_end_time_part))
        elif break_end_date or break_end_time_part:
            if 'break_end_date' not in self._errors: self.add_error('break_end_date', 'Se requiere tanto la fecha como la hora de fin de descanso.')
            if 'break_end_time_part' not in self._errors: self.add_error('break_end_time_part', 'Se requiere tanto la fecha como la hora de fin de descanso.')
            cleaned_data['combined_break_end'] = None
        else:
            cleaned_data['combined_break_end'] = None

        # Validaciones de coherencia de tiempos (server-side, como tu JS)
        start = cleaned_data.get('combined_start_time')
        end = cleaned_data.get('combined_end_time')
        b_start = cleaned_data.get('combined_break_start')
        b_end = cleaned_data.get('combined_break_end')

        if start:
            if end and end <= start:
                self.add_error('end_time_part', 'La fecha/hora de fin debe ser posterior a la de inicio.')

            if b_start and b_end:
                if b_end <= b_start:
                    self.add_error('break_end_time_part', 'El fin del descanso debe ser posterior al inicio del descanso.')

                if end:
                    if b_start and b_start < start:
                        self.add_error('break_start_time_part', 'El inicio del descanso no puede ser antes del inicio de jornada.')
                    if b_end and b_end > end:
                        self.add_error('break_end_time_part', 'El fin del descanso no puede ser después del fin de jornada.')
                    
                    if b_start and b_end:
                        if not (start <= b_start and b_end <= end):
                            if not any(error in self._errors for error in ['break_start_time_part', 'break_end_time_part']):
                                self.add_error(None, 'El descanso debe estar completamente dentro del horario de jornada.')
            elif (b_start and not b_end) or (not b_start and b_end):
                if 'break_start_time_part' not in self._errors: self.add_error('break_start_time_part', 'Se requiere el inicio y fin del descanso juntos.')
                if 'break_end_time_part' not in self._errors: self.add_error('break_end_time_part', 'Se requiere el inicio y fin del descanso juntos.')
        
        return cleaned_data

# --- FORMULARIO PARA ADMINS (ModelForm para cargar/guardar datos de TimeEntry) ---
class TimeEntryEditForm(forms.ModelForm, TimeEntryBaseFormLogic):
    # 'reason' se hereda de TimeEntryBaseFormLogic como required=False
    # Puedes añadir un campo 'notes' si TimeEntry tiene uno,
    # que es diferente del 'reason' que es para auditoría.
    # Si quieres que 'reason' sea obligatorio para el admin, descomenta y modifica:
    # reason = forms.CharField(
    #     widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
    #     label="Razón del Cambio (Admin - Obligatorio)",
    #     required=True,
    #     help_text="Debes explicar por qué realizas este cambio directo."
    # )

    class Meta:
        model = TimeEntry
        # Estos son los campos directos del modelo TimeEntry que el ModelForm mapea.
        # Los campos de fecha/hora se manejan a través de los métodos __init__ y save.
        fields = ['notes'] # 'start_time', 'end_time', 'break_start', 'break_end' se manejan aparte

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) # Esto llama al __init__ de ModelForm y luego al de TimeEntryBaseFormLogic

        # Si hay una instancia de TimeEntry (en modo edición)
        if self.instance and self.instance.pk: # Usar .pk para asegurar que es un objeto existente
            # Descomponer los campos datetime de la instancia en date y time_part
            for field_prefix, model_field_name in [
                ('start', 'start_time'),
                ('end', 'end_time'),
                ('break_start', 'break_start'),
                ('break_end', 'break_end')
            ]:
                model_value = getattr(self.instance, model_field_name)
                if model_value:
                    dt = timezone.localtime(model_value) # Asegúrate de convertir a la zona horaria local si es necesario
                    self.initial[f'{field_prefix}_date'] = dt.date()
                    self.initial[f'{field_prefix}_time_part'] = dt.time()

            # Pre-popular el campo 'reason' si hay un campo de notas de admin en TimeEntryModificationRequest
            # o si TimeEntry tiene un campo de notas de auditoría para el admin.
            # Por ahora, lo dejamos vacío ya que es una "razón para el cambio actual".
            # Si quieres que se muestre la última razón de un admin, necesitarías buscar la última modificacion_request 'approved'.
            self.initial['reason'] = '' # Siempre vacío para una nueva razón de edición

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
            if isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({'type': 'date'})
            elif isinstance(field.widget, forms.TimeInput):
                field.widget.attrs.update({'type': 'time'})
    
    
    def clean(self):
        # Primero llama al clean de ModelForm y de TimeEntryBaseFormLogic.
        # Es importante que super().clean() se llame primero para obtener los datos base.
        # Luego, llama explícitamente al clean de TimeEntryBaseFormLogic.
        cleaned_data = super().clean()

        # Ahora, llama al método clean de la clase TimeEntryBaseFormLogic
        # para que se creen los campos 'combined_...'
        # Necesitamos pasarle el formulario completo para que pueda acceder a self.errors etc.
        # Puedes llamar directamente al método 'clean' de la clase base de la siguiente manera:
        # NOTA: `super()` aquí funciona porque estamos en un contexto de herencia múltiple y queremos la siguiente clase en el MRO.
        # En este caso, queremos que el clean de TimeEntryBaseFormLogic se ejecute después del clean de ModelForm.
        cleaned_data.update(TimeEntryBaseFormLogic.clean(self))

        # --- AÑADE ESTAS LÍNEAS PARA DEPURACIÓN ADICIONAL DEL CLEAN DE ModelForm ---
        print("\n--- DEBUG (TimeEntryEditForm - clean): INICIO ---")
        print(f"DEBUG (TimeEntryEditForm - clean): Datos procesados después de ModelForm y BaseLogic: {cleaned_data}")
        print(f"DEBUG (TimeEntryEditForm - clean): Errores finales del formulario: {self.errors}")
        print("--- DEBUG (TimeEntryEditForm - clean): FIN ---\n")
        # --------------------------------------------------------------------------

        return cleaned_data
    
    
    def save(self, commit=True):
        # Llama al save del ModelForm para los campos que maneja directamente (como 'notes')
        instance = super().save(commit=False)
        
        # --- AÑADE ESTAS LÍNEAS EN EL MÉTODO save() ---
        print("\n--- DEBUG (forms.py - save): INICIO ---")
        print(f"DEBUG (forms.py - save): Instance antes de asignación: {instance.__dict__}")
        print(f"DEBUG (forms.py - save): Cleaned data recibida en save: {self.cleaned_data}")
        # -----------------------------------------------
        
        # Asignar los valores combinados al modelo TimeEntry
        if 'combined_start_time' in self.cleaned_data and self.cleaned_data['combined_start_time'] is not None:
            instance.start_time = self.cleaned_data['combined_start_time']
        if 'combined_end_time' in self.cleaned_data and self.cleaned_data['combined_end_time'] is not None:
            instance.end_time = self.cleaned_data['combined_end_time']
        if 'combined_break_start' in self.cleaned_data and self.cleaned_data['combined_break_start'] is not None:
            instance.break_start = self.cleaned_data['combined_break_start']
        if 'combined_break_end' in self.cleaned_data and self.cleaned_data['combined_break_end'] is not None:
            instance.break_end = self.cleaned_data['combined_break_end']

        # El campo 'reason' se maneja en views.py al crear la TimeEntryModificationRequest
        # si el admin ha introducido una razón.

        if commit:
            instance.save()
        return instance


# --- FORMULARIO PARA SOLICITUDES DE MODIFICACIÓN (PARA USUARIOS NO ADMINS) ---
class TimeEntryRequestModificationForm(TimeEntryBaseFormLogic):
    # Sobreescribir 'reason' para hacerlo obligatorio SOLO para solicitudes de usuario
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        label="Razón de la Solicitud (Obligatorio)",
        required=True,
        help_text="Debes explicar por qué solicitas estos cambios."
    )

    def __init__(self, *args, **kwargs):
        self.original_entry = kwargs.pop('original_entry', None) # Se pasa la instancia como original_entry
        super().__init__(*args, **kwargs)

        if self.original_entry:
            # Descomponer los campos datetime de la original_entry en date y time_part
            for field_prefix, model_field_name in [
                ('start', 'start_time'),
                ('end', 'end_time'),
                ('break_start', 'break_start'),
                ('break_end', 'break_end')
            ]:
                model_value = getattr(self.original_entry, model_field_name)
                if model_value:
                    dt = timezone.localtime(model_value) # Asegúrate de convertir a la zona horaria local si es necesario
                    self.initial[f'{field_prefix}_date'] = dt.date()
                    self.initial[f'{field_prefix}_time_part'] = dt.time()

            # La razón para una nueva solicitud de modificación siempre debe ser vacía al iniciar el form
            self.initial['reason'] = ''

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
            if isinstance(field.widget, forms.DateInput):
                field.widget.attrs.update({'type': 'date'})
            elif isinstance(field.widget, forms.TimeInput):
                field.widget.attrs.update({'type': 'time'})

    def clean(self):
        cleaned_data = super().clean()

        # Validación específica para 'reason' en este formulario (solicitud)
        reason_content = cleaned_data.get('reason')
        if not reason_content or not reason_content.strip():
            self.add_error('reason', 'La razón de la solicitud es obligatoria y no puede estar vacía.')

        return cleaned_data




# class TimeEntryEditForm(forms.ModelForm):
#     # Campos DateTimeField para fecha y hora separados para facilitar la edición en el HTML
#     start_date = forms.DateField(
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         label="Fecha Inicio"
#     )
#     start_time_part = forms.TimeField(
#         widget=forms.TimeInput(attrs={'type': 'time', 'step': '1', 'class': 'form-control'}), # Añadido step='1' para segundos si los necesitas
#         label="Hora Inicio"
#     )

#     end_date = forms.DateField(
#         required=False,
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         label="Fecha Fin"
#     )
#     end_time_part = forms.TimeField(
#         required=False,
#         widget=forms.TimeInput(attrs={'type': 'time', 'step': '1', 'class': 'form-control'}), # Añadido step='1'
#         label="Hora Fin"
#     )

#     break_start_date = forms.DateField(
#         required=False,
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         label="Fecha Inicio Descanso"
#     )
#     break_start_time_part = forms.TimeField(
#         required=False,
#         widget=forms.TimeInput(attrs={'type': 'time', 'step': '1', 'class': 'form-control'}), # Añadido step='1'
#         label="Hora Inicio Descanso"
#     )

#     break_end_date = forms.DateField(
#         required=False,
#         widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         label="Fecha Fin Descanso"
#     )
#     break_end_time_part = forms.TimeField(
#         required=False,
#         widget=forms.TimeInput(attrs={'type': 'time', 'step': '1', 'class': 'form-control'}), # Añadido step='1'
#         label="Hora Fin Descanso"
#     )

#     # Campo para la razón de la solicitud
#     reason = forms.CharField(
#         label="Razón del cambio",
#         widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#         required=False
#     )

#     class Meta:
#         model = TimeEntry
#         fields = [] # Mantenemos fields vacío ya que los manejamos manualmente.


#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         spain_tz = pytz.timezone('Europe/Madrid')

#         # Si estamos editando una instancia existente, precargamos los campos de fecha y hora
#         if self.instance and self.instance.pk: # Usar self.instance and self.instance.pk para asegurar que es una instancia existente
#             # Asegúrate de que start_time existe antes de intentar acceder a él
#             if self.instance.start_time:
#                 local_start_time = self.instance.start_time.astimezone(spain_tz)
#                 self.initial['start_date'] = local_start_time.date()
#                 self.initial['start_time_part'] = local_start_time.time()

#             if self.instance.end_time:
#                 local_end_time = self.instance.end_time.astimezone(spain_tz)
#                 self.initial['end_date'] = local_end_time.date()
#                 self.initial['end_time_part'] = local_end_time.time()

#             if self.instance.break_start:
#                 local_break_start = self.instance.break_start.astimezone(spain_tz)
#                 self.initial['break_start_date'] = local_break_start.date()
#                 self.initial['break_start_time_part'] = local_break_start.time()

#             if self.instance.break_end:
#                 local_break_end = self.instance.break_end.astimezone(spain_tz)
#                 self.initial['break_end_date'] = local_break_end.date()
#                 self.initial['break_end_time_part'] = local_break_end.time()
        
#         # Aplicar clases de Bootstrap a los campos del formulario
#         for field_name, field in self.fields.items():
#             # Ya lo estás haciendo en la definición del campo. Esto puede ser redundante
#             # o si tienes campos que no sean DateInput/TimeInput, asegúrate de que también tienen form-control.
#             # Por ejemplo, reason ya lo tiene en su definición.
#             # if isinstance(field.widget, (forms.TextInput, forms.DateInput, forms.TimeInput, forms.Textarea)):
#             #     field.widget.attrs.setdefault('class', '')
#             #     field.widget.attrs['class'] += ' form-control' # Añade la clase sin sobrescribir

#             # Si ya tienes la clase en el widget.attrs al definir el campo, puedes omitir este bucle.
#             # O asegúrate de que estás añadiendo, no sobrescribiendo, por si tienes múltiples clases.
#             # Lo dejamos así por ahora, asumiendo que es para asegurar que todos tienen form-control.
#             if 'class' not in field.widget.attrs:
#                 field.widget.attrs['class'] = 'form-control'
#             else:
#                 field.widget.attrs['class'] += ' form-control'
#             # Eliminar duplicados si se añaden múltiples veces.
#             field.widget.attrs['class'] = ' '.join(sorted(list(set(field.widget.attrs['class'].split()))))


#     def clean(self):
#         cleaned_data = super().clean()
#         spain_tz = pytz.timezone('Europe/Madrid')

#         # --- Depuración (puedes descomentar esto temporalmente) ---
#         # print("\n--- FORM CLEAN DEBUG ---")
#         # print(f"Raw POST Data for start_date: {self.data.get('start_date')}")
#         # print(f"Raw POST Data for start_time_part: {self.data.get('start_time_part')}")
#         # print(f"Cleaned Data (pre-combination) start_date: {cleaned_data.get('start_date')}")
#         # print(f"Cleaned Data (pre-combination) start_time_part: {cleaned_data.get('start_time_part')}")
#         # -----------------------------------------------------------

#         # Combinar fecha y hora para start_time (obligatorio)
#         start_date = cleaned_data.get('start_date')
#         start_time_part = cleaned_data.get('start_time_part')

#         # Añadir un flag para saber si hubo errores en la combinación
#         _start_time_combined_success = False
#         if start_date and start_time_part:
#             try:
#                 start_datetime_naive = datetime.combine(start_date, start_time_part)
#                 # Almacena el valor limpio en una clave que NO sea la del modelo directamente
#                 cleaned_data['start_time'] = timezone.make_aware(start_datetime_naive, spain_tz)
#                 _start_time_combined_success = True
#             except Exception as e:
#                 # Si hay un error al combinar, añadir error al campo específico
#                 self.add_error('start_time_part', f'Error al combinar fecha y hora de inicio: {e}. Revise el formato.')
#                 # Y asegurarse de que 'start_time' no exista en cleaned_data
#                 if 'start_time' in cleaned_data:
#                     del cleaned_data['start_time']
#         else:
#             # Si falta alguno de los dos, añadir error al campo específico
#             if not start_date:
#                 self.add_error('start_date', 'La fecha de inicio es obligatoria.')
#             if not start_time_part:
#                 self.add_error('start_time_part', 'La hora de inicio es obligatoria.')
#             # Asegurarse de que 'start_time' no exista si falta algún componente
#             if 'start_time' in cleaned_data:
#                 del cleaned_data['start_time']

#         # Combinar fecha y hora para end_time (si están presentes)
#         end_date = cleaned_data.get('end_date')
#         end_time_part = cleaned_data.get('end_time_part')
#         _end_time_combined_success = False
#         if end_date and end_time_part:
#             try:
#                 end_datetime_naive = datetime.combine(end_date, end_time_part)
#                 cleaned_data['end_time'] = timezone.make_aware(end_datetime_naive, spain_tz)
#                 _end_time_combined_success = True
#             except Exception as e:
#                 self.add_error('end_time_part', f'Error al combinar fecha y hora de fin: {e}. Revise el formato.')
#                 if 'end_time' in cleaned_data:
#                     del cleaned_data['end_time']
#         elif end_date or end_time_part: # Si solo se proporciona uno de los dos
#              self.add_error(None, "Para finalizar la jornada, se requieren tanto la fecha como la hora de fin.")
#              # No creamos el campo combinado
#              if 'end_time' in cleaned_data: # Aseguramos que no se arrastre un valor parcial
#                  del cleaned_data['end_time']
#         else:
#             cleaned_data['end_time'] = None # Permite que sea None si ambos están vacíos


#         # Combinar fecha y hora para break_start (si están presentes)
#         break_start_date = cleaned_data.get('break_start_date')
#         break_start_time_part = cleaned_data.get('break_start_time_part')
#         _break_start_combined_success = False
#         if break_start_date and break_start_time_part:
#             try:
#                 break_start_datetime_naive = datetime.combine(break_start_date, break_start_time_part)
#                 cleaned_data['break_start'] = timezone.make_aware(break_start_datetime_naive, spain_tz)
#                 _break_start_combined_success = True
#             except Exception as e:
#                 self.add_error('break_start_time_part', f'Error al combinar fecha y hora de inicio de descanso: {e}. Revise el formato.')
#                 if 'break_start' in cleaned_data:
#                     del cleaned_data['break_start']
#         elif break_start_date or break_start_time_part:
#             self.add_error(None, "Para el inicio del descanso, se requieren tanto la fecha como la hora.")
#             if 'break_start' in cleaned_data:
#                 del cleaned_data['break_start']
#         else:
#             cleaned_data['break_start'] = None


#         # Combinar fecha y hora para break_end (si están presentes)
#         break_end_date = cleaned_data.get('break_end_date')
#         break_end_time_part = cleaned_data.get('break_end_time_part')
#         _break_end_combined_success = False
#         if break_end_date and break_end_time_part:
#             try:
#                 break_end_datetime_naive = datetime.combine(break_end_date, break_end_time_part)
#                 cleaned_data['break_end'] = timezone.make_aware(break_end_datetime_naive, spain_tz)
#                 _break_end_combined_success = True
#             except Exception as e:
#                 self.add_error('break_end_time_part', f'Error al combinar fecha y hora de fin de descanso: {e}. Revise el formato.')
#                 if 'break_end' in cleaned_data:
#                     del cleaned_data['break_end']
#         elif break_end_date or break_end_time_part:
#             self.add_error(None, "Para el fin del descanso, se requieren tanto la fecha como la hora.")
#             if 'break_end' in cleaned_data:
#                 del cleaned_data['break_end']
#         else:
#             cleaned_data['break_end'] = None


#         # Validaciones de lógica de tiempos (usando los valores combinados del formulario)
#         # Solo realiza estas validaciones si los campos de tiempo principales se combinaron con éxito
#         # y si no hay errores previos que ya invalidaron el formulario.
#         if not self.errors: # Solo procede si no hay errores en los campos combinados
#             start_time = cleaned_data.get('start_time')
#             end_time = cleaned_data.get('end_time')
#             break_start = cleaned_data.get('break_start')
#             break_end = cleaned_data.get('break_end')

#             # Jornada no puede terminar antes de empezar
#             if start_time and end_time and end_time <= start_time:
#                 self.add_error('end_time_part', "La hora de fin de jornada debe ser posterior a la hora de inicio.")

#             # Descanso no puede terminar antes de empezar
#             if break_start and break_end and break_end <= break_start:
#                 self.add_error('break_end_time_part', "La hora de fin de descanso debe ser posterior a la hora de inicio de descanso.")

#             # Descanso debe estar dentro de la jornada
#             # Solo si todos los tiempos de jornada y descanso están presentes
#             if start_time and end_time and break_start and break_end:
#                 # Inicio descanso debe ser después de inicio jornada
#                 if break_start < start_time:
#                     self.add_error('break_start_time_part', "El inicio del descanso no puede ser anterior al inicio de la jornada.")
#                 # Fin descanso debe ser antes de fin jornada
#                 if break_end > end_time:
#                     self.add_error('break_end_time_part', "El fin del descanso no puede ser posterior al fin de la jornada.")
#                 # Descanso debe estar completamente dentro de la jornada (si no se han disparado los errores anteriores)
#                 if not self.errors: # Si no hay errores previos de inicio/fin de descanso
#                     if not (start_time <= break_start and break_end <= end_time):
#                         self.add_error('break_start_time_part', "El descanso debe estar completamente dentro del horario de jornada.")
#                         self.add_error('break_end_time_part', "") # Mensaje en ambos campos para claridad.
#             elif break_start and not start_time: # Si hay inicio de descanso pero no inicio de jornada (error previo)
#                  pass # El error de 'start_time' ya se manejó, no es necesario duplicar
#             elif break_end and not end_time: # Si hay fin de descanso pero no fin de jornada (error previo)
#                  pass # El error de 'end_time' ya se manejó.
            
#             # --- Validaciones de coherencia si solo se proporcionan algunos campos de descanso ---
#             if break_start and not break_end:
#                 self.add_error('break_end_time_part', 'Si se especifica el inicio de descanso, también debe especificarse el fin.')
#             if break_end and not break_start:
#                 self.add_error('break_start_time_part', 'Si se especifica el fin de descanso, también debe especificarse el inicio.')


#         # --- DEBUGGING AID: Print final cleaned_data and form errors ---
#         # print(f"Final cleaned_data: {cleaned_data}")
#         # print(f"Form errors: {self.errors}")
#         # print("--------------------------------\n")
#         # -----------------------------------------------------------

#         return cleaned_data

#     # El método save() ya estaba bien, pero lo pongo de nuevo para confirmación.
#     def save(self, commit=True):
#         instance = super().save(commit=False)

#         # Asignar los valores combinados a los campos del modelo.
#         # Asegúrate de que 'start_time' y los demás existan en cleaned_data
#         # antes de asignarlos. Usamos .get() por si hubo un error de combinación.
#         instance.start_time = self.cleaned_data.get('start_time')
#         instance.end_time = self.cleaned_data.get('end_time')
#         instance.break_start = self.cleaned_data.get('break_start')
#         instance.break_end = self.cleaned_data.get('break_end')

#         if commit:
#             instance.save()
#         return instance
    


# # ESTE ES EL FORMULARIO PARA SOLICITAR CAMBIOS
# class TimeEntryRequestModificationForm(forms.ModelForm):
#     # Definimos explícitamente los campos que el usuario va a solicitar
#     # y los conectamos con el modelo TimeEntryModificationRequest
#     # Asegúrate de que los 'requested_' fields tienen los mismos nombres en tu modelo
#     requested_start_time = forms.DateTimeField(
#         widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
#         required=False # O True, según tu lógica de si siempre debe ser enviado
#     )
#     requested_end_time = forms.DateTimeField(
#         widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
#         required=False
#     )
#     requested_break_start = forms.DateTimeField(
#         widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
#         required=False
#     )
#     requested_break_end = forms.DateTimeField(
#         widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
#         required=False
#     )
#     reason = forms.CharField(
#         widget=forms.Textarea(attrs={'rows': 3}),
#         required=True, # La razón es obligatoria para la solicitud
#         help_text="Explica por qué solicitas estos cambios."
#     )

#     class Meta:
#         model = TimeEntryModificationRequest
#         # Incluye solo los campos que el usuario llenará en el formulario de solicitud
#         fields = [
#             'requested_start_time',
#             'requested_end_time',
#             'requested_break_start',
#             'requested_break_end',
#             'reason'
#         ]

#     # Puedes añadir validaciones personalizadas aquí si lo necesitas
#     def clean(self):
#         cleaned_data = super().clean()
#         # Ejemplo: Asegurarse de que al menos un campo 'requested_' ha sido modificado
#         # o que hay datos en los campos solicitados
#         # Esta validación se haría en la vista o podrías hacerla aquí si es más general
#         return cleaned_data