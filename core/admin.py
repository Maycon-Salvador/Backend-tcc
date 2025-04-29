from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario

    list_display = ['email', 'tipo', 'is_staff', 'is_superuser']
    ordering = ['email']
    search_fields = ['email', 'cpf']

    # 🔧 Corrigido: definindo todos os fieldsets manualmente
    fieldsets = (
        ("Credenciais", {"fields": ("email", "password")}),
        ("Informações Pessoais", {"fields": (
            "tipo", "cpf", "data_nascimento", "sexo", "endereco",
            "cidade", "estado", "telefone", "crm", "especialidade"
        )}),
        ("Permissões", {"fields": (
            "is_active", "is_staff", "is_superuser", "groups", "user_permissions"
        )}),
        ("Datas Importantes", {"fields": ("last_login", "date_joined")}),
        ("Google Calendar", {"fields": (
            "google_access_token", "google_refresh_token", "google_token_expiry"
        )}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'tipo', 'password1', 'password2'),
        }),
    )
