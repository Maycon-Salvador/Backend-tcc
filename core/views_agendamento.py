from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Agendamento, Usuario
from .serializers import AgendamentoSerializer
from rest_framework import status
from rest_framework.generics import get_object_or_404
from django.utils.dateparse import parse_datetime

class MeusAgendamentosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.tipo == 'medico':
            agendamentos = Agendamento.objects.filter(medico=user)
        else:
            agendamentos = Agendamento.objects.filter(paciente=user)

        serializer = AgendamentoSerializer(agendamentos, many=True)
        return Response(serializer.data)
    
class CriarAgendamentoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user  # quem está autenticado

        try:
            # Busque o médico pelo ID que veio no JSON
            medico_id = request.data.get('medico_id')
            medico = Usuario.objects.get(id=medico_id, tipo='medico')

            agendamento = Agendamento.objects.create(
                paciente=user,
                medico=medico,
                data_hora=request.data.get('data_hora'),
                status='marcado'
            )
            serializer = AgendamentoSerializer(agendamento)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Usuario.DoesNotExist:
            return Response({'erro': 'Médico não encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'erro': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class AtualizarAgendamentoView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        agendamento = get_object_or_404(Agendamento, pk=pk)

        # Verifica se é o médico ou o paciente relacionado ao agendamento
        if request.user != agendamento.medico and request.user != agendamento.paciente:
            return Response({'erro': 'Você não tem permissão para modificar este agendamento.'}, status=403)

        # Atualiza apenas os campos enviados (parcial=True)
        serializer = AgendamentoSerializer(agendamento, data=request.data, partial=True)
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

        serializer = AgendamentoSerializer(agendamentos, many=True)
        return Response(serializer.data)