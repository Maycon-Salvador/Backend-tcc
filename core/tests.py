from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from .models import CodigoVerificacao, Agendamento, HorarioAtendimento
import json

class TestesBasicos(TestCase):
    def setUp(self):
        """Configuração inicial para todos os testes"""
        self.client = APIClient()
        self.Usuario = get_user_model()
        
        # Criar usuário comum
        self.usuario = self.Usuario.objects.create_user(
            email='teste@exemplo.com',
            password='senha123',
            nome='Usuário Teste',
            tipo='comum',
            cpf='12345678900'
        )
        
        # Criar médico
        self.medico = self.Usuario.objects.create_user(
            email='medico@exemplo.com',
            password='senha123',
            nome='Dr. Teste',
            tipo='medico',
            crm='12345',
            especialidade='Clínico Geral',
            cpf='98765432100'
        )

class TestesAutenticacao(TestesBasicos):
    def test_registro_sucesso(self):
        """Testa registro de usuário com sucesso"""
        dados = {
            'email': 'novo@exemplo.com',
            'password': 'senha123',
            'nome': 'Novo Usuário',
            'tipo': 'comum',
            'cpf': '11122233344',
            'data_nascimento': '1990-01-01',
            'sexo': 'M',
            'endereco': 'Rua Teste, 123',
            'cidade': 'Cidade Teste',
            'estado': 'Estado Teste',
            'telefone': '11999999999'
        }
        
        response = self.client.post('/register/', dados)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('mensagem', response.data)
        
        # Verifica se o usuário foi criado
        usuario = self.Usuario.objects.filter(email=dados['email']).first()
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.nome, dados['nome'])
        self.assertEqual(usuario.cpf, dados['cpf'])

    def test_registro_cpf_duplicado(self):
        """Testa registro com CPF já cadastrado"""
        dados = {
            'email': 'outro@exemplo.com',
            'password': 'senha123',
            'nome': 'Outro Usuário',
            'tipo': 'comum',
            'cpf': self.usuario.cpf,  # CPF já cadastrado
            'data_nascimento': '1990-01-01',
            'sexo': 'M',
            'endereco': 'Rua Teste, 123',
            'cidade': 'Cidade Teste',
            'estado': 'Estado Teste',
            'telefone': '11999999999'
        }
        
        response = self.client.post('/register/', dados)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['erro'], 'CPF já cadastrado.')

    def test_login_sucesso(self):
        """Testa login com sucesso"""
        response = self.client.post('/api/token/', {
            'email': self.usuario.email,
            'password': 'senha123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

class TestesHorarioAtendimento(TestesBasicos):
    def setUp(self):
        super().setUp()
        # Login como médico
        self.client.force_authenticate(user=self.medico)

    def test_criar_horario(self):
        """Testa a criação de horário de atendimento"""
        dados = {
            'dia_semana': 'segunda',
            'horarios': ['09:00', '10:00', '11:00'],
            'local': 'Consultório 1',
            'duracao_consulta_minutos': 30,
            'intervalo_consulta_minutos': 10,
            'indisponivel': False
        }
        
        response = self.client.post('/horarios-atendimento/', dados, format='json')
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verifica se o horário foi criado
        horario = HorarioAtendimento.objects.first()
        self.assertIsNotNone(horario)
        self.assertEqual(horario.medico, self.medico)
        self.assertEqual(horario.dia_semana, 'segunda')
        self.assertEqual(horario.local, 'Consultório 1')
        self.assertEqual(horario.horarios, ['09:00', '10:00', '11:00'])
        self.assertEqual(horario.duracao_consulta_minutos, 30)
        self.assertEqual(horario.intervalo_consulta_minutos, 10)
        self.assertEqual(horario.indisponivel, False)

    def test_criar_horario_paciente(self):
        """Testa se paciente não pode criar horário"""
        # Login como paciente
        self.client.force_authenticate(user=self.usuario)
        
        dados = {
            'dia_semana': 'segunda',
            'horarios': ['09:00', '10:00', '11:00'],
            'local': 'Consultório 1',
            'duracao_consulta_minutos': 30,
            'intervalo_consulta_minutos': 10,
            'indisponivel': False
        }
        
        response = self.client.post('/horarios-atendimento/', dados, format='json')
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class TestesAgendamento(TestesBasicos):
    def setUp(self):
        super().setUp()
        # Login como paciente
        self.client.force_authenticate(user=self.usuario)
        
        # Criar horário de atendimento para o médico
        self.horario = HorarioAtendimento.objects.create(
            medico=self.medico,
            dia_semana='SEGUNDA',
            horarios=['09:00', '10:00', '11:00'],
            local='Consultório 1',
            duracao_consulta_minutos=30,
            intervalo_consulta_minutos=0
        )

    def test_criar_agendamento(self):
        """Testa a criação de um agendamento"""
        data_hora = timezone.now() + timedelta(days=1)
        data_hora = data_hora.replace(hour=9, minute=0, second=0, microsecond=0)
        
        response = self.client.post('/agendamentos/', {
            'medico_id': str(self.medico.id),
            'data_hora': data_hora.isoformat(),
            'observacoes': 'Consulta de teste'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verifica se o agendamento foi criado
        agendamento = Agendamento.objects.first()
        self.assertIsNotNone(agendamento)
        self.assertEqual(agendamento.paciente, self.usuario)
        self.assertEqual(agendamento.medico, self.medico)
        self.assertEqual(agendamento.status, 'solicitado')

    def test_criar_agendamento_sem_medico(self):
        """Testa criação de agendamento sem médico"""
        data_hora = timezone.now() + timedelta(days=1)
        
        response = self.client.post('/agendamentos/', {
            'data_hora': data_hora.isoformat(),
            'observacoes': 'Consulta de teste'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('medico_id', response.data['erro'].lower())

    def test_atualizar_status_agendamento(self):
        """Testa a atualização do status do agendamento"""
        # Cria um agendamento
        agendamento = Agendamento.objects.create(
            paciente=self.usuario,
            medico=self.medico,
            data_hora=timezone.now() + timedelta(days=1),
            status='solicitado'
        )
        
        # Login como médico
        self.client.force_authenticate(user=self.medico)
        
        # Atualiza o status
        response = self.client.patch(f'/agendamentos/{agendamento.id}/status/', {
            'status': 'agendado'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verifica se o status foi atualizado
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, 'agendado')

    def test_listar_agendamentos(self):
        """Testa a listagem de agendamentos"""
        # Cria alguns agendamentos
        Agendamento.objects.create(
            paciente=self.usuario,
            medico=self.medico,
            data_hora=timezone.now() + timedelta(days=1),
            status='solicitado'
        )
        
        Agendamento.objects.create(
            paciente=self.usuario,
            medico=self.medico,
            data_hora=timezone.now() + timedelta(days=2),
            status='agendado'
        )
        
        # Lista agendamentos
        response = self.client.get('/meus-agendamentos/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_cancelar_agendamento(self):
        """Testa o cancelamento de um agendamento"""
        # Cria um agendamento
        agendamento = Agendamento.objects.create(
            paciente=self.usuario,
            medico=self.medico,
            data_hora=timezone.now() + timedelta(days=1),
            status='agendado'
        )
        
        # Login como médico
        self.client.force_authenticate(user=self.medico)
        
        # Cancela o agendamento
        response = self.client.post(f'/agendamentos/{agendamento.id}/cancelar/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'agendamento cancelado')
        
        # Verifica se o status foi atualizado
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, 'cancelado')

    def test_cancelar_agendamento_sem_permissao(self):
        """Testa o cancelamento de um agendamento sem permissão"""
        # Cria um agendamento
        agendamento = Agendamento.objects.create(
            paciente=self.usuario,
            medico=self.medico,
            data_hora=timezone.now() + timedelta(days=1),
            status='agendado'
        )
        
        # Cria outro usuário sem permissão
        outro_usuario = self.Usuario.objects.create_user(
            email='outro@exemplo.com',
            password='senha123',
            nome='Outro Usuário',
            tipo='comum',
            cpf='11122233344'
        )
        
        # Login como outro usuário
        self.client.force_authenticate(user=outro_usuario)
        
        # Tenta cancelar o agendamento
        response = self.client.post(f'/agendamentos/{agendamento.id}/cancelar/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verifica se o status não foi alterado
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, 'agendado')
