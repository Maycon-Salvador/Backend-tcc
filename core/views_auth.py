from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from .models import Usuario
from .serializers import UsuarioSerializer
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from .serializers import MeuTokenSerializer

@api_view(['POST'])
def register(request):
    data = request.data
    email = data.get('email')
    password = data.get('password')
    tipo = data.get('tipo', 'comum')  # padrão para comum

    if Usuario.objects.filter(email=email).exists():
        return Response({'erro': 'E-mail já está em uso'}, status=400)

    user = Usuario.objects.create_user(
        email=email,
        password=password,
        tipo=tipo,
        cpf=data.get('cpf', ''),
        data_nascimento=data.get('data_nascimento'),
        sexo=data.get('sexo', ''),
        endereco=data.get('endereco', ''),
        cidade=data.get('cidade', ''),
        estado=data.get('estado', ''),
        telefone=data.get('telefone', ''),
        crm=data.get('crm', '') if tipo == 'medico' else '',
        especialidade=data.get('especialidade', '') if tipo == 'medico' else '',
    )

    return Response({'mensagem': 'Usuário registrado com sucesso'})


@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user is not None:
        return Response({'mensagem': 'Login realizado com sucesso!', 'user': UsuarioSerializer(user).data})
    return Response({'erro': 'Usuário ou senha inválidos'}, status=401)



class MinhaContaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "mensagem": "Você está autenticado!",
            "usuario": request.user.username,
            "tipo": request.user.tipo,
        })
        
class LoginComCookieView(TokenObtainPairView):
    serializer_class = MeuTokenSerializer
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            access = response.data['access']
            refresh = response.data['refresh']

            response.set_cookie(
                key="access_token",
                value=access,
                httponly=True,
                samesite="Lax"
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh,
                httponly=True,
                samesite="Lax"
            )
        
        return response
    
@api_view(["POST"])
def validar_cpf(request):
    cpf = request.data.get("cpf")

    if not cpf:
        return Response({"erro": "CPF é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

    if Usuario.objects.filter(cpf=cpf).exists():
        return Response({"erro": "CPF já cadastrado."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"mensagem": "CPF válido."}, status=status.HTTP_200_OK)

@api_view(["POST"])
def validar_email(request):
    email = request.data.get("email")

    if not email:
        return Response({"erro": "E-mail é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

    if Usuario.objects.filter(email=email).exists():
        return Response({"erro": "E-mail já cadastrado."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"mensagem": "E-mail válido."}, status=status.HTTP_200_OK)
