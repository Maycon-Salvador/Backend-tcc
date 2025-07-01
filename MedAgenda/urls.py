from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views import (
    TestViewSet, home_view, CustomTokenObtainPairView,
    enviar_codigo, validar_codigo, criar_superusuario,
    resetar_senha, HorarioAtendimentoViewSet, ListarMedicosView,
    AgendamentoViewSet, enviar_email_agendamento
)
from core.views_auth import (
    MinhaContaView, MedicoMeView, FotoUsuarioView,
    verificar_senha, verificar_sessao, register, validar_email
)
from core.views_agendamento import (
    AtualizarStatusAgendamentoView, UploadAnexoView,
    DownloadAnexoEspecificoView, DeletarAnexoView,
    CriarAgendamentoView, MeusAgendamentosView, CancelarAgendamentoView
)
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt

router = DefaultRouter()
router.register(r'test', TestViewSet, basename='test')
router.register(r'horarios-atendimento', HorarioAtendimentoViewSet, basename='horarios-atendimento')
# Removendo a rota de agendamentos do router para evitar conflito
# router.register(r'agendamentos', AgendamentoViewSet, basename='agendamentos')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view),
    
    # Inclui as rotas do router
    path('', include(router.urls)),
    
    # Autenticação e Usuário
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', register, name='register'),
    path('validar-email/', validar_email, name='validar_email'),
    path('enviar-codigo/', csrf_exempt(enviar_codigo), name='enviar_codigo'),
    path('verificar-codigo/', validar_codigo, name='verificar_codigo'),
    path('minha-conta/', MinhaContaView.as_view(), name='minha_conta'),
    path('usuarios/me/foto/', FotoUsuarioView.as_view(), name='usuario_foto'),
    
    # Recuperação de Senha
    path('recuperar-senha/', resetar_senha, name='resetar_senha'),
    path('verificar-codigo-recuperacao/', validar_codigo, name='verificar_codigo_recuperacao'),
    path('alterar-senha/', resetar_senha, name='alterar_senha'),
    
    # Agendamento
    path('agendamentos/', CriarAgendamentoView.as_view(), name='criar_agendamento'),
    path('agendamentos/<uuid:pk>/status/', AtualizarStatusAgendamentoView.as_view(), name='atualizar_status_agendamento'),
    path('agendamentos/<uuid:pk>/cancelar/', CancelarAgendamentoView.as_view(), name='cancelar_agendamento'),
    path('meus-agendamentos/', MeusAgendamentosView.as_view(), name='meus_agendamentos'),
    path('enviar-email/', enviar_email_agendamento, name='enviar_email'),
    
    # Anexos
    path('agendamentos/<uuid:pk>/anexos/upload/', csrf_exempt(UploadAnexoView.as_view()), name='upload-anexo'),
    path('agendamentos/anexos/<int:pk>/download/', DownloadAnexoEspecificoView.as_view(), name='download-anexo-especifico'),
    path('agendamentos/anexos/<int:pk>/deletar/', csrf_exempt(DeletarAnexoView.as_view()), name='deletar-anexo'),
    
    # Médico
    path('medico/me/', MedicoMeView.as_view(), name='medico_me'),
    
    # Especialistas
    path('medicos/', ListarMedicosView.as_view(), name='listar_medicos'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
