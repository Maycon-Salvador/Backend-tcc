from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer, AgendamentoSerializer
from django.core.management import call_command
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from .models import CodigoVerificacao, Agendamento
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import CodigoVerificacao
import random
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import viewsets, permissions, generics
from rest_framework.permissions import AllowAny
import logging
from rest_framework import status


# views.py
from .models import HorarioAtendimento
from .serializers import HorarioAtendimentoSerializer

# ViewSet de teste
class TestViewSet(viewsets.ViewSet):
    def list(self, request):
        return Response({"mensagem": "Olá do TestViewSet!"})

    @action(detail=False)
    def custom_action(self, request):
        return Response({"mensagem": "Ação customizada do TestViewSet!"})


# Nova view para a raiz
def home_view(request):
    return HttpResponse("Bem-vindo ao backend MedAgenda!")


# View de login com JWT
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer



@api_view(['POST'])
def enviar_codigo(request):
    """
    Endpoint para enviar código de verificação.
    Pode ser usado tanto para registro quanto para recuperação de senha.
    
    Requer:
    - email: email do usuário
    - tipo: 'registro' ou 'recuperacao' (opcional, padrão é 'recuperacao')
    """
    email = request.data.get("email")
    tipo = request.data.get("tipo", "recuperacao")  # padrão é recuperação
    Usuario = get_user_model()  # Movido para o início da função

    if not email:
        return Response({"erro": "O campo email é obrigatório."}, status=400)

    # Verifica se o usuário existe apenas para recuperação de senha
    if tipo == "recuperacao":
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response({"erro": "Usuário não encontrado."}, status=404)
    else:
        # Para registro, verifica se o email já está cadastrado
        if Usuario.objects.filter(email=email).exists():
            return Response({"erro": "E-mail já cadastrado."}, status=400)

    try:
        # Remove códigos anteriores
        CodigoVerificacao.objects.filter(email=email).delete()

        # Gera novo código
        novo_codigo = get_random_string(length=6, allowed_chars='0123456789')

        # Salva novo código
        CodigoVerificacao.objects.create(email=email, codigo=novo_codigo)

        # Prepara a mensagem baseada no tipo
        if tipo == "recuperacao":
            subject = 'Código de verificação - Recuperação de Senha'
            message = f"""
            Olá {usuario.nome or 'Usuário'},

            Você solicitou a recuperação de senha no MedAgenda.
            Seu código de verificação é: {novo_codigo}

            Este código é válido por 30 minutos.
            Se você não solicitou esta recuperação de senha, por favor ignore este email.

            Atenciosamente,
            Equipe MedAgenda
            """
        else:  # registro
            subject = 'Código de verificação - Cadastro'
            message = f"""
            Olá,

            Bem-vindo ao MedAgenda!
            Seu código de verificação para completar o cadastro é: {novo_codigo}

            Este código é válido por 30 minutos.
            Use-o para confirmar seu cadastro em nossa plataforma.

            Atenciosamente,
            Equipe MedAgenda
            """

        # Envia o código
        send_mail(
            subject=subject,
            message=message,
            from_email='medagendasistema@gmail.com',
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({
            "mensagem": "Código enviado com sucesso para o e-mail.",
            "email": email,
            "tipo": tipo
        })

    except Exception as e:
        logger.error(f"Erro ao enviar código de verificação: {str(e)}")
        return Response({"erro": "Erro ao enviar código de verificação. Tente novamente mais tarde."}, status=500)

@api_view(['POST'])
def validar_codigo(request):
    email = request.data.get("email")
    codigo = request.data.get("codigo")

    try:
        registro = CodigoVerificacao.objects.get(email=email, codigo=codigo)
        if not registro.esta_valido():
            return Response({"erro": "Código expirado."}, status=400)

        return Response({"mensagem": "Código válido!"})

    except CodigoVerificacao.DoesNotExist:
        return Response({"erro": "Código inválido."}, status=400)




@api_view(["POST"])
def criar_superusuario(request):
    User = get_user_model()

    if User.objects.filter(is_superuser=True).exists():
        return Response({"erro": "Já existe um superusuário."}, status=400)

    User.objects.create(
        email="admin@medagenda.com",
        password=make_password("admin123"),
        is_superuser=True,
        is_staff=True,
        is_active=True,
        tipo="medico",  # ou "comum", dependendo do seu model
        
    )

    return Response({"mensagem": "Superusuário criado com sucesso."})




@api_view(['POST'])
def resetar_senha(request):
    """
    Endpoint para resetar a senha do usuário.
    Requer:
    - email: email do usuário
    - codigo: código de verificação
    - nova_senha: nova senha a ser definida
    """
    email = request.data.get("email")
    codigo = request.data.get("codigo")
    nova_senha = request.data.get("nova_senha")

    # Validações iniciais
    if not email:
        return Response({"erro": "O campo email é obrigatório."}, status=400)
    if not codigo:
        return Response({"erro": "O campo código é obrigatório."}, status=400)
    if not nova_senha:
        return Response({"erro": "O campo nova_senha é obrigatório."}, status=400)

    # Validação da senha
    if len(nova_senha) < 8:
        return Response({"erro": "A senha deve ter pelo menos 8 caracteres."}, status=400)

    try:
        # Verifica se o código é válido
        codigo_verificacao = CodigoVerificacao.objects.get(email=email, codigo=codigo)
        if not codigo_verificacao.esta_valido():
            return Response({"erro": "Código expirado. Por favor, solicite um novo código."}, status=400)

        # Busca o usuário
        Usuario = get_user_model()
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response({"erro": "Usuário não encontrado."}, status=404)

        # Atualiza a senha
        usuario.password = make_password(nova_senha)
        usuario.save()

        # Remove o código de verificação usado
        codigo_verificacao.delete()

        return Response({
            "mensagem": "Senha atualizada com sucesso!",
            "email": email
        })

    except CodigoVerificacao.DoesNotExist:
        return Response({"erro": "Código inválido. Verifique o código e tente novamente."}, status=400)
    except Exception as e:
        logger.error(f"Erro ao resetar senha: {str(e)}")
        return Response({"erro": "Erro ao processar a solicitação. Tente novamente mais tarde."}, status=500)


logger = logging.getLogger(__name__)

class HorarioAtendimentoViewSet(viewsets.ModelViewSet):
    queryset = HorarioAtendimento.objects.select_related('medico').all()
    serializer_class = HorarioAtendimentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        logger.info(f"=== Iniciando busca de horários ===")
        logger.info(f"Usuário autenticado: {self.request.user}")
        logger.info(f"Token de autenticação: {self.request.auth}")
        logger.info(f"Cabeçalhos da requisição: {self.request.headers}")
        
        # Se for médico, retorna apenas seus horários
        if hasattr(self.request.user, 'tipo') and self.request.user.tipo == 'medico':
            logger.info(f"Usuário é médico, retornando seus horários")
            queryset = self.queryset.filter(medico=self.request.user)
        else:
            # Se não for médico, retorna todos os horários (para visualização)
            logger.info(f"Usuário não é médico, retornando todos os horários para visualização")
            queryset = self.queryset.all()
        
        logger.info(f"Encontrados {queryset.count()} horários")
        
        # Log detalhado de cada horário encontrado
        for horario in queryset:
            logger.info(f"""
                Horário encontrado:
                - ID: {horario.id}
                - Médico ID: {horario.medico.id}
                - Médico: {horario.medico.email}
                - Dia: {horario.dia_semana}
                - Horários: {horario.horarios}
                - Local: {horario.local}
                - Indisponível: {horario.indisponivel}
                - Duração consulta: {horario.duracao_consulta_minutos}min
                - Intervalo: {horario.intervalo_consulta_minutos}min
            """)
        
        return queryset

    def create(self, request, *args, **kwargs):
        logger.info(f"=== Criando novo horário de atendimento ===")
        logger.info(f"Usuário: {request.user}")
        logger.info(f"Dados recebidos: {request.data}")
        
        # Apenas médicos podem criar horários
        if not hasattr(request.user, 'tipo') or request.user.tipo != 'medico':
            logger.error(f"Usuário {request.user} não é um médico")
            return Response(
                {"erro": "Apenas médicos podem criar horários de atendimento"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                horario = serializer.save(medico=request.user)
                logger.info(f"Horário criado com sucesso: {horario.id}")
                logger.info(f"Dados do horário criado: {serializer.data}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Erro ao criar horário: {str(e)}")
                return Response(
                    {"erro": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        logger.info(f"=== Atualizando horário de atendimento ===")
        logger.info(f"Usuário: {request.user}")
        logger.info(f"Dados recebidos: {request.data}")
        
        # Verifica se o usuário é o médico dono do horário
        horario = self.get_object()
        if request.user != horario.medico:
            logger.error(f"Usuário {request.user} não tem permissão para atualizar este horário")
            raise permissions.PermissionDenied("Você só pode atualizar seus próprios horários")
        
        response = super().update(request, *args, **kwargs)
        logger.info(f"Horário atualizado com sucesso: {response.data}")
        return response

    def destroy(self, request, *args, **kwargs):
        logger.info(f"=== Deletando horário de atendimento ===")
        logger.info(f"Usuário: {request.user}")
        logger.info(f"ID do horário: {kwargs.get('pk')}")
        
        # Verifica se o usuário é o médico dono do horário
        horario = self.get_object()
        if request.user != horario.medico:
            logger.error(f"Usuário {request.user} não tem permissão para deletar este horário")
            raise permissions.PermissionDenied("Você só pode deletar seus próprios horários")
        
        response = super().destroy(request, *args, **kwargs)
        logger.info("Horário deletado com sucesso")
        return response

class ListarMedicosView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = None  # Vamos criar o serializer depois

    def get_queryset(self):
        User = get_user_model()
        return User.objects.filter(tipo='medico', is_active=True).select_related()

    def get_serializer_class(self):
        from .serializers import MedicoSerializer
        return MedicoSerializer

class AgendamentoViewSet(viewsets.ModelViewSet):
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            # Busque o médico pelo UUID que veio no JSON
            medico_id = request.data.get('medico_id')
            if not medico_id:
                return Response({'erro': 'O campo medico_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

            medico = get_user_model().objects.get(id=medico_id, tipo='medico')
            
            # Valida data_hora
            data_hora = request.data.get('data_hora')
            if not data_hora:
                return Response({'erro': 'O campo data_hora é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

            # Cria o agendamento
            agendamento = Agendamento.objects.create(
                paciente=request.user,
                medico=medico,
                data_hora=data_hora,
                status='solicitado'
            )

            # Envia email de notificação para o médico
            try:
                # Envia email diretamente
                send_mail(
                    subject='Nova solicitação de agendamento',
                    message=f"""
                    Olá Dr(a). {medico.nome},
                    
                    Você recebeu uma nova solicitação de agendamento:
                    
                    Paciente: {request.user.nome}
                    Data e Hora: {data_hora}
                    
                    Acesse sua agenda para confirmar ou recusar este agendamento.
                    
                    Atenciosamente,
                    Equipe MedAgenda
                    """,
                    from_email='medagendasistema@gmail.com',
                    recipient_list=[medico.email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Erro ao enviar email de solicitação: {str(e)}")

            serializer = self.get_serializer(agendamento)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except get_user_model().DoesNotExist:
            return Response({'erro': 'Médico não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'erro': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def aceitar(self, request, pk=None):
        """
        Aceita um agendamento e envia email para o paciente.
        """
        agendamento = self.get_object()
        agendamento.status = 'agendado'
        agendamento.save()
        
        # Envia email de confirmação para o paciente
        try:
            send_mail(
                subject='Seu agendamento foi confirmado',
                message=f"""
                Olá {agendamento.paciente.nome},
                
                Seu agendamento foi confirmado:
                
                Médico: Dr(a). {agendamento.medico.nome}
                Data e Hora: {agendamento.data_hora}
                
                Não se esqueça de sua consulta!
                
                Atenciosamente,
                Equipe MedAgenda
                """,
                from_email='medagendasistema@gmail.com',
                recipient_list=[agendamento.paciente.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Erro ao enviar email de confirmação: {str(e)}")
        
        return Response({'status': 'agendamento aceito'})

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """
        Cancela um agendamento e envia email para o paciente.
        """
        agendamento = self.get_object()
        
        # Verifica se é o médico ou o paciente relacionado ao agendamento
        if request.user != agendamento.medico and request.user != agendamento.paciente:
            return Response({'erro': 'Você não tem permissão para cancelar este agendamento.'}, status=status.HTTP_403_FORBIDDEN)
        
        agendamento.status = 'cancelado'
        agendamento.save()
        
        # Envia email de cancelamento para o paciente
        try:
            send_mail(
                subject='Seu agendamento foi cancelado',
                message=f"""
                Olá {agendamento.paciente.nome},
                
                Seu agendamento foi cancelado:
                
                Médico: Dr(a). {agendamento.medico.nome}
                Data e Hora: {agendamento.data_hora}
                
                Caso queira reagendar, acesse nossa plataforma.
                
                Atenciosamente,
                Equipe MedAgenda
                """,
                from_email='medagendasistema@gmail.com',
                recipient_list=[agendamento.paciente.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Erro ao enviar email de cancelamento: {str(e)}")
        
        return Response({'status': 'agendamento cancelado'})

@api_view(['POST'])
def enviar_email_agendamento(request):
    """
    Endpoint para enviar emails de notificação sobre agendamentos.
    Recebe:
    - tipo: 'solicitacao' ou 'confirmacao'
    - agendamento_id: ID do agendamento (opcional, se não fornecido, usa o último agendamento criado)
    """
    tipo = request.data.get('tipo', 'solicitacao')
    agendamento_id = request.data.get('agendamento_id')
    
    try:
        if agendamento_id:
            agendamento = Agendamento.objects.get(id=agendamento_id)
        else:
            # Se não fornecido, pega o último agendamento criado
            agendamento = Agendamento.objects.latest('id')
    except Agendamento.DoesNotExist:
        return Response({"erro": "Agendamento não encontrado"}, status=404)
    
    if tipo == 'solicitacao':
        # Email para o médico sobre nova solicitação
        subject = 'Nova solicitação de agendamento'
        message = f"""
        Olá Dr(a). {agendamento.medico.nome},
        
        Você recebeu uma nova solicitação de agendamento:
        
        Paciente: {agendamento.paciente.nome}
        Data e Hora: {agendamento.data_hora}
        Motivo: {agendamento.observacoes}
        
        Acesse sua agenda para confirmar ou recusar este agendamento.
        
        Atenciosamente,
        Equipe MedAgenda
        """
        recipient = agendamento.medico.email
        
    elif tipo == 'confirmacao':
        # Email para o paciente sobre confirmação
        subject = 'Seu agendamento foi confirmado'
        message = f"""
        Olá {agendamento.paciente.nome},
        
        Seu agendamento foi confirmado:
        
        Médico: Dr(a). {agendamento.medico.nome}
        Data e Hora: {agendamento.data_hora}
        Motivo: {agendamento.observacoes}
        
        Não se esqueça de sua consulta!
        
        Atenciosamente,
        Equipe MedAgenda
        """
        recipient = agendamento.paciente.email
        
    else:
        return Response({"erro": "Tipo de email inválido"}, status=400)
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email='medagendasistema@gmail.com',
            recipient_list=[recipient],
            fail_silently=False,
        )
        return Response({"mensagem": "Email enviado com sucesso"})
    except Exception as e:
        logger.error(f"Erro ao enviar email: {str(e)}")
        return Response({"erro": "Falha ao enviar email"}, status=500)
