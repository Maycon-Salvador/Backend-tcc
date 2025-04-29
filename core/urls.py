
from django.urls import path
from .views_auth import register, login_view, MinhaContaView, validar_cpf, validar_email
from .views_agendamento import CriarAgendamentoView,AtualizarAgendamentoView, DeletarAgendamentoView,MeusAgendamentosView
from .views_google import google_login, google_redirect, criar_evento_google
from .views import CustomTokenObtainPairView
from .views import enviar_codigo_verificacao, verificar_codigo



urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('minha-conta/', MinhaContaView.as_view(), name='minha_conta'),
    path('meus-agendamentos/', MeusAgendamentosView.as_view(), name='meus_agendamentos'),
    path('agendamentos/criar/', CriarAgendamentoView.as_view(), name='criar_agendamento'),
    path('agendamentos/<int:pk>/atualizar/', AtualizarAgendamentoView.as_view(), name='atualizar-agendamento'),
    path('agendamentos/<int:pk>/deletar/', DeletarAgendamentoView.as_view(), name='deletar-agendamento'),
     # Google Calendar
    path('google/login/', google_login, name='google_login'),
    path('google/redirect/', google_redirect, name='google_redirect'),
    path('google/agenda/criar/', criar_evento_google, name='criar_evento_google'),
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("enviar-codigo/", enviar_codigo_verificacao),
    path("verificar-codigo/", verificar_codigo),
    path('validar-cpf/', validar_cpf),
    path("validar-email/", validar_email),

]
from .views import criar_superusuario

urlpatterns += [
    path("criar-superuser/", criar_superusuario),
]
