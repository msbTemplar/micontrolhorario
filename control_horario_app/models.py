from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import pytz

# Nuevo modelo para la Empresa
class Company(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Nombre de la Empresa")
    code = models.CharField(max_length=50, unique=True, verbose_name="Código de la Empresa")
    # Puedes añadir más campos aquí si lo necesitas, por ejemplo:
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, null=True, verbose_name="Email de Contacto")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.name + f" ({self.code})"

# Modificar el modelo User para incluir la relación con Company
# Opción 1: Si no has extendido el User de Django, añade un OneToOneField a un Profile
# (Esta es la opción recomendada para no modificar el User directamente)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL, # Si la empresa se elimina, los usuarios de esa empresa tendrían 'company' a null
        null=True,
        blank=True, # Puede ser null, por ejemplo, hasta que se asigne una empresa
        verbose_name="Empresa Asociada"
    )
    # Puedes añadir otros campos de perfil aquí si los necesitas
    # ejemplo_campo = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"

    def __str__(self):
        return f"Perfil de {self.user.username}"

class TimeEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    break_start = models.DateTimeField(null=True, blank=True)
    break_end = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False) # Considerar añadir esto para auditoría
    last_edited = models.DateTimeField(null=True, blank=True) # Y esto

    def __str__(self):
        return f"{self.user.username} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-start_time'] # Esto ya debería estar

    @property
    def duration(self):
        """
        Calcula la duración neta de la jornada en horas, descontando el descanso.
        Retorna None si la jornada no ha finalizado.
        """
        if self.start_time and self.end_time:
            total_work_seconds = (self.end_time - self.start_time).total_seconds()
            
            break_seconds = 0
            if self.break_start and self.break_end:
                # Asegurarse de que el descanso no exceda la jornada (aunque lógicamente no debería pasar)
                break_duration = (self.break_end - self.break_start).total_seconds()
                break_seconds = max(0, break_duration) # Asegurarse de que no sea negativo

            net_duration_seconds = total_work_seconds - break_seconds
            return max(0, net_duration_seconds / 3600) # Convertir a horas y asegurar que no sea negativo
        return None # Retorna None si la jornada no está finalizada


# >>>>>>>>>>>>> TU MODELO ACTUALIZADO PARA SOLICITUDES DE MODIFICACIÓN <<<<<<<<<<<<<
class TimeEntryModificationRequest(models.Model):
    original_entry = models.ForeignKey(TimeEntry, on_delete=models.CASCADE, related_name='modification_requests')
    requesting_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_modification_requests')

    # Almacenar los valores propuestos para los campos
    requested_start_time = models.DateTimeField()
    requested_end_time = models.DateTimeField(null=True, blank=True)
    requested_break_start = models.DateTimeField(null=True, blank=True)
    requested_break_end = models.DateTimeField(null=True, blank=True)
    
    # Campo para la razón de la solicitud
    reason = models.TextField(blank=True, null=True, help_text="Razón para la solicitud de cambio.")

    # Estado de la solicitud
    REQUEST_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobada'),
        ('rejected', 'Rechazada'),
    ]
    status = models.CharField(max_length=10, choices=REQUEST_STATUS_CHOICES, default='pending')
    
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_modification_requests')
    
    # ***** CAMBIO IMPORTANTE: AÑADIR ESTE CAMPO *****
    admin_notes = models.TextField(blank=True, null=True, help_text="Notas del administrador al revisar la solicitud.")
    
    def __str__(self):
        return f"Solicitud de {self.requesting_user.username} para Entry ID {self.original_entry.id} - {self.status}"
    
    class Meta:
        ordering = ['-requested_at']