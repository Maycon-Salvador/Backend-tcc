from rest_framework import serializers
from .models import Usuario, Agendamento
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'  # ou liste todos os campos usados no cadastro
    def to_representation(self, instance):
        data = super().to_representation(instance)
        cpf = data.get("cpf", "")
        if len(cpf) == 11:
            # Formata para 000.000.000-00
            data["cpf"] = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return data

    def validate_cpf(self, value):
        """
        Verifica se o CPF é válido e único.
        """
        # Remove pontos e traços
        cpf = re.sub(r"[^\d]", "", value)

        # CPF deve ter 11 dígitos
        if len(cpf) != 11 or not cpf.isdigit():
            raise serializers.ValidationError("CPF inválido.")

        # Rejeita CPFs com dígitos repetidos (ex: 111.111.111-11)
        if cpf == cpf[0] * 11:
            raise serializers.ValidationError("CPF inválido.")

        # Verifica se já existe
        if Usuario.objects.filter(cpf=cpf).exists():
            raise serializers.ValidationError("CPF já cadastrado.")

        return cpf

class AgendamentoSerializer(serializers.ModelSerializer):
    paciente = UsuarioSerializer(read_only=True)
    medico = UsuarioSerializer(read_only=True)

    class Meta:
        model = Agendamento
        fields = ['id', 'paciente', 'medico', 'data_hora', 'status', 'observacoes']
class MeuTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Adiciona o ID (ou uuid) no payload do token
        token["user_id"] = str(user.id)
        token["email"] = user.email  # ou qualquer campo válido

        token["tipo"] = user.tipo
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Adiciona os dados do usuário na resposta (além do token)
        data["user"] = {
            "id": str(self.user.id),  # ou self.user.uuid se tiver
            "email": self.user.email,
            "tipo": self.user.tipo,
        }
        return data

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        if email:
            attrs["username"] = email
        return super().validate(attrs)


    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['tipo'] = user.tipo  # se quiser incluir o tipo no token
        return token
