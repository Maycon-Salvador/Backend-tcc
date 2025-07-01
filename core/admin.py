from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, HorarioAtendimento, Agendamento, AnexoAgendamento

# Inlines para HorarioAtendimento e Agendamento
class HorarioAtendimentoInline(admin.TabularInline):
    model = HorarioAtendimento
    extra = 1 # Quantidade de formulários extras em branco para adicionar
    fields = ['dia_semana', 'local', 'horarios', 'indisponivel', 'duracao_consulta_minutos', 'intervalo_consulta_minutos'] # Adicione os novos campos aqui

# Inline para AnexoAgendamento no Agendamento
class AnexoAgendamentoInline(admin.TabularInline):
    model = AnexoAgendamento
    extra = 0
    readonly_fields = ['nome_arquivo', 'data_upload'] # Você pode adicionar download links aqui se precisar
    fields = ['nome_arquivo', 'data_upload', 'arquivo']


class AgendamentoMedicoInline(admin.TabularInline):
    model = Agendamento
    fk_name = 'medico' # Especifica o campo ForeignKey no modelo Agendamento que aponta para o médico (Usuario)
    extra = 0 # Não adicionar formulários extras para agendamentos existentes
    readonly_fields = ['paciente', 'data_hora', 'status', 'observacoes'] # Campos somente para leitura
    can_delete = False # Não permitir deletar agendamentos por aqui


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario

    list_display = ['nome', 'email', 'tipo', 'is_staff', 'is_superuser']
    ordering = ['email']
    search_fields = ['email', 'cpf', 'nome']

    # 🔧 Corrigido: definindo todos os fieldsets manualmente
    fieldsets = (
        ("Credenciais", {"fields": ("email", "password")}),
        ("Informações Pessoais", {"fields": (
            "tipo", "cpf", "data_nascimento", "sexo", "endereco",
            "cidade", "estado", "telefone", "crm", "especialidade",
            "nome"
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

    # Sobrescrever get_inline para mostrar inlines condicionalmente
    def get_inline(self, request, obj=None):
        # Se for um superusuário ou um usuário médico, inclua o inline de horários
        if obj and obj.tipo == 'medico':
            return [HorarioAtendimentoInline, AgendamentoMedicoInline]
        # Para outros usuários, apenas o inline de agendamentos como paciente (se você criar um)
        # Por enquanto, para usuários comuns, nenhum inline relacionado a agendamentos como médico
        return [AgendamentoMedicoInline] if obj and obj.tipo == 'medico' else []


# Registrar Agendamento (agora com inline de anexos)
@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'paciente', 'medico', 'data_hora', 'status']
    search_fields = ['paciente__email', 'medico__email']
    list_filter = ['status', 'data_hora']
    date_hierarchy = 'data_hora'
    inlines = [AnexoAgendamentoInline] # Adicionar inline de anexos aqui

    fieldsets = (
        (None, {
            'fields': (
                'id', # Campo ID somente leitura
                'paciente',
                'medico',
                'data_hora',
                'status',
                'observacoes', # Adicionando observacoes para visualização/edição
            ),
        }),
    )
    readonly_fields = ['id']


# Manter AnexoAgendamentoAdmin se ainda quiser gerenciar anexos diretamente, caso contrário remova
# @admin.register(AnexoAgendamento)
# class AnexoAgendamentoAdmin(admin.ModelAdmin):
#     list_display = ['agendamento', 'nome_arquivo', 'data_upload']
#     search_fields = ['agendamento__paciente__email', 'agendamento__medico__email', 'nome_arquivo']
#     list_filter = ['data_upload']
