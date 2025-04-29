from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.contrib.auth.models import BaseUserManager


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
    email = models.EmailField(unique=True)
    tipo = models.CharField(max_length=20, choices=[("comum", "Comum"), ("medico", "Médico")])
    username = None
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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['tipo']

    objects = UsuarioManager()

    # 🔑 Campos para integração com Google Calendar
    google_access_token = models.TextField(blank=True, null=True)
    google_refresh_token = models.TextField(blank=True, null=True)
    google_token_expiry = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.email} ({self.get_tipo_display()})"


    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'


# ✅ Modelo de Agendamento de consultas
class Agendamento(models.Model):
    STATUS_CHOICES = [
        ('marcado', 'Marcado'),
        ('cancelado', 'Cancelado'),
        ('recusado', 'Recusado'),
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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='marcado')
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.paciente.email} com {self.medico.email} em {self.data_hora}"

