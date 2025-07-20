from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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