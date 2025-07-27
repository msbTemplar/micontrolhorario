from django.contrib import admin
from .models import TimeEntry, TimeEntryModificationRequest, Company, UserProfile # Importa Company y UserProfile
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives # <- Aquí se importa
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Opcional: Para mostrar Company y UserProfile en el admin
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code','address','phone','email', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('created_at',)

# Para integrar UserProfile en la administración de usuarios de Django
class UserProfileInline(admin.StackedInline): # O admin.TabularInline si prefieres una vista de tabla
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = BaseUserAdmin.list_display + ('get_company_name',) # Añade la empresa a la lista de usuarios

    def get_company_name(self, obj):
        return obj.profile.company.name if hasattr(obj, 'profile') and obj.profile.company else '-'
    get_company_name.short_description = 'Empresa'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Si es superuser, ve todo
        if request.user.is_superuser:
            return qs

        # Si es staff pero no superuser: ocultar usuarios superusuarios
        return qs.exclude(is_superuser=True)

# Re-registra el modelo User para usar tu UserAdmin personalizado
admin.site.unregister(User)
admin.site.register(User, UserAdmin)



# Registra tu modelo TimeEntry
@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_time', 'end_time', 'duration', 'notes', 'is_edited', 'last_edited')
    list_filter = ('user', 'is_edited', 'start_time')
    search_fields = ('user__username', 'notes')
    date_hierarchy = 'start_time'
    # Campos que puedes editar directamente en la lista
    list_editable = ('is_edited',)

# Registra el nuevo modelo de solicitud de modificación
@admin.register(TimeEntryModificationRequest)
class TimeEntryModificationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'original_entry_link', 'requesting_user', 'status', 
        'requested_start_time', 'requested_end_time', 
        'requested_break_start', 'requested_break_end',
        'reason', 'requested_at', 'reviewer_display'
    )
    list_filter = ('status', 'requesting_user', 'requested_at')
    search_fields = ('requesting_user__username', 'original_entry__user__username', 'reason')
    raw_id_fields = ('original_entry', 'requesting_user', 'reviewer') 
    date_hierarchy = 'requested_at'
    readonly_fields = ('requested_at', 'reviewed_at', 'reviewer') # Estos campos solo se llenan automáticamente o por el sistema

    # Campos que se muestran en el detalle de la solicitud (form_fields)
    # y los campos de los valores propuestos
    fieldsets = (
        (None, {
            'fields': ('original_entry', 'requesting_user', 'status', 'reason')
        }),
        ('Valores Originales de la Jornada', {
            'fields': (
                ('original_entry_start_time', 'original_entry_end_time'),
                ('original_entry_break_start', 'original_entry_break_end'),
                'original_entry_notes',
            ),
            'classes': ('collapse',), # Puedes hacer que se colapsen por defecto
        }),
        ('Valores Solicitados', {
            'fields': (
                ('requested_start_time', 'requested_end_time'),
                ('requested_break_start', 'requested_break_end'),
            )
        }),
        ('Revisión', {
            'fields': ('reviewer', 'reviewed_at'),
            'description': 'Información sobre quién y cuándo revisó la solicitud.'
        })
    )

    # Añadir campos de solo lectura para mostrar el valor original en el formulario de admin
    def get_readonly_fields(self, request, obj=None):
        if obj: # Solo cuando se edita un objeto existente
            return self.readonly_fields + (
                'original_entry', 'requesting_user', 'requested_start_time', 
                'requested_end_time', 'requested_break_start', 'requested_break_end', 'reason'
            )
        return self.readonly_fields

    # Métodos para mostrar información adicional en la lista y detalle
    def original_entry_link(self, obj):
        if obj.original_entry:
            from django.utils.html import format_html
            from django.urls import reverse
            link = reverse("admin:%s_%s_change" % (obj.original_entry._meta.app_label, obj.original_entry._meta.model_name), args=[obj.original_entry.id])
            return format_html('<a href="{}">{}</a>', link, f"Entry ID: {obj.original_entry.id} ({obj.original_entry.user.username})")
        return "-"
    original_entry_link.short_description = "Registro Original"

    def reviewer_display(self, obj):
        return obj.reviewer.username if obj.reviewer else "-"
    reviewer_display.short_description = "Revisor"

    # Campos de solo lectura para mostrar los valores originales en el fieldset
    def original_entry_start_time(self, obj):
        return timezone.localtime(obj.original_entry.start_time).strftime('%Y-%m-%d %H:%M')
    original_entry_start_time.short_description = "Original Start"

    def original_entry_end_time(self, obj):
        return timezone.localtime(obj.original_entry.end_time).strftime('%Y-%m-%d %H:%M') if obj.original_entry.end_time else "N/A"
    original_entry_end_time.short_description = "Original End"

    def original_entry_break_start(self, obj):
        return timezone.localtime(obj.original_entry.break_start).strftime('%Y-%m-%d %H:%M') if obj.original_entry.break_start else "N/A"
    original_entry_break_start.short_description = "Original Break Start"

    def original_entry_break_end(self, obj):
        return timezone.localtime(obj.original_entry.break_end).strftime('%Y-%m-%d %H:%M') if obj.original_entry.break_end else "N/A"
    original_entry_break_end.short_description = "Original Break End"

    def original_entry_notes(self, obj):
        return obj.original_entry.notes
    original_entry_notes.short_description = "Original Notes"


    # Acciones personalizadas para aprobar/rechazar
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        # Asegúrate de que solo se procesen solicitudes pendientes
        pending_requests = queryset.filter(status='pending')
        updated_count = 0
        for req in pending_requests:
            # Aplicar los cambios al TimeEntry original
            req.original_entry.start_time = req.requested_start_time
            req.original_entry.end_time = req.requested_end_time
            req.original_entry.break_start = req.requested_break_start
            req.original_entry.break_end = req.requested_break_end
            req.original_entry.is_edited = True # Marcar el original como editado
            req.original_entry.last_edited = timezone.now()
            req.original_entry.save()

            # Actualizar el estado de la solicitud
            req.status = 'approved'
            req.reviewed_at = timezone.now()
            req.reviewer = request.user
            req.save()
            updated_count += 1
            
            # Opcional: Enviar un correo al usuario notificando la aprobación
            self._send_approval_rejection_email(req, 'approved')

        self.message_user(request, f"{updated_count} solicitudes aprobadas y aplicadas a los registros de jornada.")
    approve_requests.short_description = "Aprobar solicitudes seleccionadas y aplicar cambios"

    def reject_requests(self, request, queryset):
        pending_requests = queryset.filter(status='pending')
        updated_count = 0
        for req in pending_requests:
            req.status = 'rejected'
            req.reviewed_at = timezone.now()
            req.reviewer = request.user
            req.save()
            updated_count += 1

            # Opcional: Enviar un correo al usuario notificando el rechazo
            self._send_approval_rejection_email(req, 'rejected')

        self.message_user(request, f"{updated_count} solicitudes rechazadas.")
    reject_requests.short_description = "Rechazar solicitudes seleccionadas"

    # Función auxiliar para enviar correos de aprobación/rechazo
    def _send_approval_rejection_email(self, request_obj, status):
        subject = f"Su solicitud de modificación de jornada ha sido {status.upper()}"
        
        template_name = 'control_horario_app/user_request_status_email.html' # Nueva plantilla
        
        context = {
            'requesting_user': request_obj.requesting_user,
            'original_entry': request_obj.original_entry,
            'modification_request': request_obj, # Pasa la solicitud completa
            'status': status,
            'admin_notes': '', # El admin podría añadir notas al aprobar/rechazar
            'company_name': 'Tu Empresa',
            'site_url_logo': 'https://i.imgur.com/oNrnCFF.jpeg', # Tu logo
        }

        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)

        email = EmailMultiAlternatives(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [request_obj.requesting_user.email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=True) # Fail silently para evitar errores en el admin al enviar correos