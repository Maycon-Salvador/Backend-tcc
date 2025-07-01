from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from datetime import timedelta
import uuid

class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório')
        email = self.normalize_email(email)
        #extra_fields.setdefault('username', email)  # usa e-mail como username
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

# ✅ Modelo customizado de usuário com campos Google incluídos
class Usuario(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    tipo = models.CharField(max_length=20, choices=[("comum", "Comum"), ("medico", "Médico")])
    username = None
    nome = models.CharField(max_length=255, blank=True)
    cpf = models.CharField(
    max_length=11,  # apenas os números, sem pontos ou traços
    unique=True,
    blank=False,
    null=False
)
    data_nascimento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=20, blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=100, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    crm = models.CharField(max_length=20, blank=True)
    especialidade = models.CharField(max_length=100, blank=True)
    foto = models.ImageField(upload_to='fotos_usuarios/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['tipo']

    objects = UsuarioManager()

    # 🔑 Campos para integração com Google Calendar
    google_access_token = models.TextField(blank=True, null=True)
    google_refresh_token = models.TextField(blank=True, null=True)
    google_token_expiry = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.email} ({self.get_tipo_display()})"

    @property
    def full_name(self):
        """
        Retorna o nome completo combinando first_name e last_name.
        """
        # Concatena first_name e last_name, tratando casos onde um ou ambos são nulos/vazios
        full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return full_name if full_name else "Nome não informado"

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'


# ✅ Modelo de Agendamento de consultas
class Agendamento(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    STATUS_CHOICES = [
        ('solicitado', 'Agendamento Solicitado'),
        ('pendente', 'Pendente de Confirmação'),
        ('agendado', 'Agendado'),
        ('cancelado', 'Cancelado'),
        ('concluido', 'Concluído'),
    ]

    paciente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agendamentos_paciente'
    )

    medico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='agendamentos_medico'
    )

    data_hora = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='solicitado')
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.paciente.email} com {self.medico.email} em {self.data_hora}"

class CodigoVerificacao(models.Model):
    email = models.EmailField()
    codigo = models.CharField(max_length=6)
    criado_em = models.DateTimeField(auto_now_add=True)

    def esta_valido(self):
        return timezone.now() < self.criado_em + timedelta(minutes=30)

    
class HorarioAtendimento(models.Model):
    medico = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='horarios_atendimento')
    local = models.CharField(max_length=255)

    DIAS_SEMANA = [
        ('segunda', 'Segunda'),
        ('terca', 'Terça'),
        ('quarta', 'Quarta'),
        ('quinta', 'Quinta'),
        ('sexta', 'Sexta'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
    ]
    dia_semana = models.CharField(max_length=10, choices=DIAS_SEMANA)
    horarios = models.JSONField()  # Salva os horários como lista de strings, ex: ["07:00", "07:40"]
    indisponivel = models.BooleanField(default=False)
    duracao_consulta_minutos = models.IntegerField(default=30) # Campo para a duração da consulta em minutos
    intervalo_consulta_minutos = models.IntegerField(default=10) # Campo para o intervalo entre consultas em minutos

    def __str__(self):
        return f"{self.medico.email} - {self.dia_semana}"

class AnexoAgendamento(models.Model):
    agendamento = models.ForeignKey(Agendamento, on_delete=models.CASCADE, related_name='anexos')
    arquivo = models.FileField(upload_to='anexos_agendamento/')
    nome_arquivo = models.CharField(max_length=255)  # Armazena o nome original do arquivo
    data_upload = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Anexo de {self.agendamento} - {self.nome_arquivo}"

    class Meta:
        verbose_name = 'Anexo de Agendamento'
        verbose_name_plural = 'Anexos de Agendamento'

