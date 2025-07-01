from rest_framework import serializers
from .models import Usuario, Agendamento, HorarioAtendimento, AnexoAgendamento
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import re

class UsuarioSerializer(serializers.ModelSerializer):
    foto_url = serializers.SerializerMethodField()
    foto = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'tipo', 'cpf', 'data_nascimento', 'sexo', 'endereco', 'cidade', 'estado', 'telefone', 'crm', 'especialidade', 'nome', 'foto', 'foto_url']

    def validate_email(self, value):
        """
        Verifica se o email é válido e único.
        """
        if not value:
            raise serializers.ValidationError("O email é obrigatório.")
        
        # Verifica se o email já está cadastrado
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("E-mail já cadastrado.")
        
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        cpf = data.get("cpf", "")
        if len(cpf) == 11:
            # Formata para 000.000.000-00
            data["cpf"] = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        
        # Garante que foto_url seja sempre incluído
        data['foto_url'] = self.get_foto_url(instance)
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

    def get_foto_url(self, obj):
        request = self.context.get('request')
        if obj.foto and hasattr(obj.foto, 'url'):
            if request:
                return request.build_absolute_uri(obj.foto.url)
            return obj.foto.url
        return None

    def update(self, instance, validated_data):
        # Se uma nova foto foi enviada, remove a antiga
        if 'foto' in validated_data:
            if instance.foto:
                instance.foto.delete(save=False)
        return super().update(instance, validated_data)

class UsuarioUpdateSerializer(serializers.ModelSerializer):
    foto_url = serializers.SerializerMethodField()
    foto = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'tipo', 'cpf', 'data_nascimento', 'sexo', 'endereco', 'cidade', 'estado', 'telefone', 'crm', 'especialidade', 'nome', 'foto', 'foto_url']
        read_only_fields = ['email', 'tipo', 'cpf']  # Campos que não podem ser alterados

    def get_foto_url(self, obj):
        request = self.context.get('request')
        if obj.foto and hasattr(obj.foto, 'url'):
            if request:
                return request.build_absolute_uri(obj.foto.url)
            return obj.foto.url
        return None

    def update(self, instance, validated_data):
        # Se uma nova foto foi enviada, remove a antiga
        if 'foto' in validated_data:
            if instance.foto:
                instance.foto.delete(save=False)
        return super().update(instance, validated_data)

class AnexoAgendamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnexoAgendamento
        fields = ['id', 'arquivo', 'nome_arquivo']

class AgendamentoSerializer(serializers.ModelSerializer):
    paciente = UsuarioSerializer(read_only=True)
    medico = UsuarioSerializer(read_only=True)
    anexos = AnexoAgendamentoSerializer(many=True, read_only=True)

    class Meta:
        model = Agendamento
        fields = ['id', 'paciente', 'medico', 'data_hora', 'status', 'observacoes', 'anexos']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Garante que o contexto seja passado para os serializers aninhados
        if 'request' in self.context:
            data['medico'] = UsuarioSerializer(instance.medico, context=self.context).data
            data['paciente'] = UsuarioSerializer(instance.paciente, context=self.context).data
        return data

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
        data = super().validate(attrs)
        
        # Adiciona os dados do usuário na resposta
        data["user"] = {
            "id": str(self.user.id),
            "email": self.user.email,
            "tipo": self.user.tipo,
        }
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['tipo'] = user.tipo
        token['user_id'] = str(user.id)  # Adiciona o ID do usuário no token
        return token

class HorarioAtendimentoSerializer(serializers.ModelSerializer):
    medico_id = serializers.UUIDField(source='medico.id', read_only=True)
    medico_nome = serializers.CharField(source='medico.nome', read_only=True)
    medico_email = serializers.EmailField(source='medico.email', read_only=True)
    medico_especialidade = serializers.CharField(source='medico.especialidade', read_only=True)

    class Meta:
        model = HorarioAtendimento
        fields = [
            'id',
            'medico_id',
            'medico_nome',
            'medico_email',
            'medico_especialidade',
            'local',
            'dia_semana',
            'horarios',
            'indisponivel',
            'duracao_consulta_minutos',
            'intervalo_consulta_minutos'
        ]
        read_only_fields = ['medico_id', 'medico_nome', 'medico_email', 'medico_especialidade']

    def validate_dia_semana(self, value):
        """Valida se o dia da semana é válido"""
        dias_validos = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
        if value.lower() not in dias_validos:
            raise serializers.ValidationError(f"Dia da semana inválido. Use um dos seguintes: {', '.join(dias_validos)}")
        return value.lower()

    def validate_horarios(self, value):
        """Valida se os horários estão no formato correto"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Horários deve ser uma lista")
        
        for horario in value:
            if not isinstance(horario, str):
                raise serializers.ValidationError("Cada horário deve ser uma string")
            try:
                hora, minuto = map(int, horario.split(':'))
                if not (0 <= hora <= 23 and 0 <= minuto <= 59):
                    raise ValueError
            except ValueError:
                raise serializers.ValidationError(f"Horário inválido: {horario}. Use o formato HH:MM")
        
        return value

    def validate(self, data):
        """Validações adicionais"""
        if data.get('duracao_consulta_minutos', 0) <= 0:
            raise serializers.ValidationError("A duração da consulta deve ser maior que zero")
        
        if data.get('intervalo_consulta_minutos', 0) < 0:
            raise serializers.ValidationError("O intervalo entre consultas não pode ser negativo")
        
        return data

class MedicoSerializer(serializers.ModelSerializer):
    foto_url = serializers.SerializerMethodField()
    horarios_atendimento = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'email', 'nome', 'crm', 'especialidade', 'foto_url', 'horarios_atendimento']

    def get_foto_url(self, obj):
        request = self.context.get('request')
        if obj.foto and hasattr(obj.foto, 'url'):
            if request:
                return request.build_absolute_uri(obj.foto.url)
            return obj.foto.url
        return None

    def get_horarios_atendimento(self, obj):
        dias_semana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
        horarios = {}
        
        # Inicializa todos os dias com lista vazia
        for dia in dias_semana:
            horarios[dia] = []
        
        # Preenche com os horários existentes
        for horario in obj.horarios_atendimento.all():
            horarios[horario.dia_semana] = horario.horarios
        
        return horarios
