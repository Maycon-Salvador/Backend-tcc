from django.urls import path
from .views_auth import register, login_view, MinhaContaView, validar_cpf, validar_email, MedicoMeView, FotoUsuarioView, verificar_senha, verificar_sessao
from .views_agendamento import CriarAgendamentoView, AtualizarAgendamentoView, DeletarAgendamentoView, MeusAgendamentosView, UploadAnexoView, DownloadAnexoEspecificoView, DeletarAnexoView, AtualizarStatusAgendamentoView
from .views_google import google_login, google_redirect, criar_evento_google
from .views import CustomTokenObtainPairView
from .views import enviar_codigo as enviar_codigo_verificacao, validar_codigo as verificar_codigo
from .views import resetar_senha
from .views_verificacao import send_code_view
from rest_framework.routers import DefaultRouter
from .views import HorarioAtendimentoViewSet, TestViewSet, ListarMedicosView
from .views import criar_superusuario
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt

router = DefaultRouter()
router.register(r'horarios-atendimento', HorarioAtendimentoViewSet, basename='horarios-atendimento')
router.register(r'test', TestViewSet, basename='test')

# Rotas do aplicativo core (diretas)
core_urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('minha-conta/', MinhaContaView.as_view(), name='minha_conta'),
    path('usuarios/verificar-senha/', verificar_senha, name='verificar_senha'),
    path('usuarios/verificar-sessao/', verificar_sessao, name='verificar_sessao'),
    path('meus-agendamentos/', MeusAgendamentosView.as_view(), name='meus_agendamentos'),
    path('agendamentos/criar/', CriarAgendamentoView.as_view(), name='criar_agendamento'),
    path('agendamentos/<uuid:pk>/atualizar/', AtualizarAgendamentoView.as_view(), name='atualizar-agendamento'),
    path('agendamentos/<int:pk>/status/', AtualizarStatusAgendamentoView.as_view(), name='atualizar-status-agendamento'),
    path('agendamentos/<uuid:pk>/status/', AtualizarStatusAgendamentoView.as_view(), name='atualizar-status-agendamento-uuid'),
    path('agendamentos/<uuid:pk>/deletar/', DeletarAgendamentoView.as_view(), name='deletar-agendamento'),
    path('agendamentos/<uuid:pk>/anexos/upload/', csrf_exempt(UploadAnexoView.as_view()), name='upload-anexo'),
    path('agendamentos/anexos/<int:pk>/download/', DownloadAnexoEspecificoView.as_view(), name='download-anexo-especifico'),
    path('agendamentos/anexos/<int:pk>/deletar/', csrf_exempt(DeletarAnexoView.as_view()), name='deletar-anexo'),
    path('medico/me/', MedicoMeView.as_view(), name='medico_me'),
    path('medicos/', ListarMedicosView.as_view(), name='listar_medicos'),
    # Google Calendar
    path('google/login/', google_login, name='google_login'),
    path('google/redirect/', google_redirect, name='google_redirect'),
    path('google/agenda/criar/', criar_evento_google, name='criar_evento_google'),
    path("enviar-codigo/", enviar_codigo_verificacao),
    path("verificar-codigo/", verificar_codigo),
    path('validar-cpf/', validar_cpf),
    path("validar-email/", validar_email),
    path("send-code/", send_code_view),
    path("resetar-senha/", resetar_senha, name="resetar_senha"),
    path("criar-superuser/", criar_superusuario),
    path('usuarios/me/foto/', FotoUsuarioView.as_view(), name='upload-foto-usuario'),
]

# Rotas do router
router_urlpatterns = router.urls

# Serve media files during development
if settings.DEBUG:
    core_urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# urlpatterns principal (manteremos para compatibilidade)
urlpatterns = core_urlpatterns + router_urlpatterns



