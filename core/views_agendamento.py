from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Agendamento, Usuario, AnexoAgendamento
from .serializers import AgendamentoSerializer, AnexoAgendamentoSerializer
from rest_framework import status
from rest_framework.generics import get_object_or_404
from django.utils.dateparse import parse_datetime
from uuid import UUID
from django.http import FileResponse, Http404
import os
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

class MeusAgendamentosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Base: paciente ou médico
        if user.tipo == 'medico':
            agendamentos = Agendamento.objects.filter(medico=user)
        else:
            agendamentos = Agendamento.objects.filter(paciente=user)

        # Filtro por status
        status_param = request.query_params.get('status')
        if status_param:
            agendamentos = agendamentos.filter(status=status_param)

        # Filtro por faixa de data
        data_inicial = request.query_params.get('data_inicial')
        data_final = request.query_params.get('data_final')
        if data_inicial:
            agendamentos = agendamentos.filter(data_hora__gte=parse_datetime(data_inicial))
        if data_final:
            agendamentos = agendamentos.filter(data_hora__lte=parse_datetime(data_final))

        serializer = AgendamentoSerializer(agendamentos, many=True, context={'request': request})
        return Response(serializer.data)
    
class CriarAgendamentoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # quem está autenticado

        try:
            # Validação dos campos obrigatórios
            medico_id = request.data.get('medico_id')
            if not medico_id:
                return Response({'erro': 'O campo medico_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

            data_hora = request.data.get('data_hora')
            if not data_hora:
                return Response({'erro': 'O campo data_hora é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

            # Busque o médico pelo UUID que veio no JSON
            try:
                medico = Usuario.objects.get(id=medico_id, tipo='medico')
            except Usuario.DoesNotExist:
                return Response({'erro': 'Médico não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

            # Cria o agendamento
            agendamento = Agendamento.objects.create(
                paciente=user,
                medico=medico,
                data_hora=data_hora,
                status='solicitado',
                observacoes=request.data.get('observacoes', '')
            )

            # Envia email de notificação para o médico
            try:
                send_mail(
                    subject='Nova solicitação de agendamento',
                    message=f"""
                    Olá Dr(a). {medico.nome},
                    
                    Você recebeu uma nova solicitação de agendamento:
                    
                    Paciente: {user.nome}
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

            serializer = AgendamentoSerializer(agendamento, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Erro ao criar agendamento: {str(e)}")
            return Response({'erro': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class AtualizarAgendamentoView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        agendamento = get_object_or_404(Agendamento, pk=pk)

        # Verifica se é o médico ou o paciente relacionado ao agendamento
        if request.user != agendamento.medico and request.user != agendamento.paciente:
            return Response({'erro': 'Você não tem permissão para modificar este agendamento.'}, status=403)

        # Atualiza apenas os campos enviados (parcial=True)
        serializer = AgendamentoSerializer(agendamento, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
class DeletarAgendamentoView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        agendamento = get_object_or_404(Agendamento, pk=pk)

        if request.user != agendamento.medico and request.user != agendamento.paciente:
            return Response({'erro': 'Você não tem permissão para deletar este agendamento.'}, status=403)

        agendamento.delete()
        return Response({'mensagem': 'Agendamento excluído com sucesso.'}, status=204)

class UploadAnexoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        agendamento = get_object_or_404(Agendamento, pk=pk)

        # Check permission: only related medico or paciente can upload attachments
        if request.user != agendamento.medico and request.user != agendamento.paciente:
            return Response({'erro': 'Você não tem permissão para adicionar anexos a este agendamento.'}, status=status.HTTP_403_FORBIDDEN)

        # Allow multiple file uploads
        uploaded_files = request.FILES.getlist('arquivos') # 'arquivos' is the expected field name in the form data
        if not uploaded_files:
            return Response({'erro': 'Nenhum arquivo enviado.'}, status=status.HTTP_400_BAD_REQUEST)

        anexos = []
        for uploaded_file in uploaded_files:
            anexo = AnexoAgendamento.objects.create(
                agendamento=agendamento,
                arquivo=uploaded_file,
                nome_arquivo=uploaded_file.name # Save the original filename
            )
            anexos.append(anexo)

        # Serialize the created attachments
        serializer = AnexoAgendamentoSerializer(anexos, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class DownloadAnexoEspecificoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            # Get the specific attachment object by its primary key (the AnexoAgendamento's pk)
            anexo = AnexoAgendamento.objects.get(pk=pk)
        except AnexoAgendamento.DoesNotExist:
            raise Http404("Anexo não encontrado.")

        # Verify permission: only the medico or paciente related to the Agendamento can download the attachment
        agendamento = anexo.agendamento
        if request.user != agendamento.medico and request.user != agendamento.paciente:
            return Response({'erro': 'Você não tem permissão para baixar este anexo.'}, status=status.HTTP_403_FORBIDDEN)

        if not anexo.arquivo:
             return Response({'erro': 'Este anexo não possui arquivo associado.'}, status=status.HTTP_404_NOT_FOUND)

        # Serve the file
        try:
            filepath = anexo.arquivo.path
            # Use the saved original filename
            filename = anexo.nome_arquivo if anexo.nome_arquivo else os.path.basename(filepath)
            return FileResponse(open(filepath, 'rb'), filename=filename)
        except FileNotFoundError:
            return Response({'erro': 'Arquivo não encontrado no servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeletarAnexoView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            # Get the specific attachment object by its primary key (the AnexoAgendamento's pk)
            anexo = AnexoAgendamento.objects.get(pk=pk)
        except AnexoAgendamento.DoesNotExist:
            return Response({'erro': 'Anexo não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Verify permission: only the medico or paciente related to the Agendamento can delete the attachment
        agendamento = anexo.agendamento
        if request.user != agendamento.medico and request.user != agendamento.paciente:
            return Response({'erro': 'Você não tem permissão para deletar este anexo.'}, status=status.HTTP_403_FORBIDDEN)

        # Delete the attachment file from the filesystem and the database object
        anexo.delete()

        return Response({'mensagem': 'Anexo excluído com sucesso.'}, status=status.HTTP_204_NO_CONTENT)

class AtualizarStatusAgendamentoView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            # Garante que pk é string antes de manipular
            pk_str = str(pk)
            try:
                pk_uuid = UUID(pk_str)
            except ValueError:
                pk_uuid = pk_str  # Se não for UUID, mantém como está

            agendamento = get_object_or_404(Agendamento, pk=pk_uuid)

            # Verifica se é o médico ou o paciente relacionado ao agendamento
            if request.user != agendamento.medico and request.user != agendamento.paciente:
                return Response({'erro': 'Você não tem permissão para modificar este agendamento.'}, status=403)

            # Verifica se o status está presente nos dados da requisição
            novo_status = request.data.get('status')
            if not novo_status:
                return Response({'erro': 'O campo status é obrigatório.'}, status=400)

            # Verifica se o status é válido
            if novo_status not in dict(Agendamento.STATUS_CHOICES):
                return Response({'erro': 'Status inválido.'}, status=400)

            # Atualiza apenas o status
            agendamento.status = novo_status
            agendamento.save()

            # Envia email baseado no novo status
            try:
                if novo_status == 'agendado':
                    # Email de confirmação para o paciente
                    subject = 'Seu agendamento foi confirmado'
                    message = f"""
                    Olá {agendamento.paciente.nome},
                    
                    Seu agendamento foi confirmado:
                    
                    Médico: Dr(a). {agendamento.medico.nome}
                    Data e Hora: {agendamento.data_hora}
                    
                    Não se esqueça de sua consulta!
                    
                    Atenciosamente,
                    Equipe MedAgenda
                    """
                    recipient = agendamento.paciente.email
                
                elif novo_status == 'cancelado':
                    # Email de cancelamento para o paciente
                    subject = 'Seu agendamento foi cancelado'
                    message = f"""
                    Olá {agendamento.paciente.nome},
                    
                    Seu agendamento foi cancelado:
                    
                    Médico: Dr(a). {agendamento.medico.nome}
                    Data e Hora: {agendamento.data_hora}
                    
                    Caso queira reagendar, acesse nossa plataforma.
                    
                    Atenciosamente,
                    Equipe MedAgenda
                    """
                    recipient = agendamento.paciente.email

                # Envia o email se houver um destinatário definido
                if 'recipient' in locals():
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email='medagendasistema@gmail.com',
                        recipient_list=[recipient],
                        fail_silently=False,
                    )
            except Exception as e:
                logger.error(f"Erro ao enviar email: {str(e)}")

            serializer = AgendamentoSerializer(agendamento, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            return Response({'erro': str(e)}, status=400)

class CancelarAgendamentoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            # Garante que pk é string antes de manipular
            pk_str = str(pk)
            try:
                pk_uuid = UUID(pk_str)
            except ValueError:
                pk_uuid = pk_str  # Se não for UUID, mantém como está

            agendamento = get_object_or_404(Agendamento, pk=pk_uuid)

            # Verifica se é o médico ou o paciente relacionado ao agendamento
            if request.user != agendamento.medico and request.user != agendamento.paciente:
                return Response({'erro': 'Você não tem permissão para cancelar este agendamento.'}, status=status.HTTP_403_FORBIDDEN)

            # Atualiza o status para cancelado
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

        except Exception as e:
            logger.error(f"Erro ao cancelar agendamento: {str(e)}")
            return Response({'erro': str(e)}, status=status.HTTP_400_BAD_REQUEST)