from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from .models import Usuario
from .serializers import UsuarioSerializer, UsuarioUpdateSerializer
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from .serializers import MeuTokenSerializer
from django.db import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

@api_view(['POST'])
def register(request):
    data = request.data
    email = data.get('email')
    print(f"Email recebido no cadastro: {email}")
    
    # Usa o serializer para validação
    serializer = UsuarioSerializer(data=data)
    if not serializer.is_valid():
        # Verifica especificamente o erro de CPF
        if 'cpf' in serializer.errors:
            return Response({"erro": "CPF já cadastrado."}, status=400)
        # Verifica especificamente o erro de email
        if 'email' in serializer.errors:
            return Response({"erro": "E-mail já cadastrado."}, status=400)
        # Para outros erros, retorna todos os erros do serializer
        return Response(serializer.errors, status=400)
    
    try:
        # Cria o usuário com os dados validados
        user = Usuario.objects.create_user(
            email=email,
            password=data.get('password'),
            tipo=data.get('tipo', 'comum'),
            cpf=serializer.validated_data['cpf'],
            data_nascimento=data.get('data_nascimento'),
            sexo=data.get('sexo', ''),
            endereco=data.get('endereco', ''),
            cidade=data.get('cidade', ''),
            estado=data.get('estado', ''),
            telefone=data.get('telefone', ''),
            crm=data.get('crm', '') if data.get('tipo') == 'medico' else '',
            especialidade=data.get('especialidade', '') if data.get('tipo') == 'medico' else '',
            nome=data.get('nome', ''),
        )
        return Response({'mensagem': 'Usuário registrado com sucesso'}, status=201)
    except IntegrityError as e:
        if "cpf" in str(e):
            return Response({"erro": "CPF já cadastrado."}, status=400)
        if "email" in str(e):
            return Response({"erro": "E-mail já cadastrado."}, status=400)
        return Response({"erro": "Erro de integridade no cadastro."}, status=400)
    except Exception as e:
        return Response({"erro": str(e)}, status=500)


@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user is not None:
        return Response({
            'mensagem': 'Login realizado com sucesso!',
            'user': {
                'uuid': str(user.id),
                'email': user.email,
                'tipo': user.tipo,
            }
        })
    return Response({'erro': 'Usuário ou senha inválidos'}, status=401)



class MinhaContaView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        serializer = UsuarioSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def put(self, request):
        serializer = UsuarioUpdateSerializer(request.user, data=request.data, partial=False, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request):
        serializer = UsuarioUpdateSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

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

    return Response({"mensagem": "E-mail válido para cadastro."}, status=status.HTTP_200_OK)

class MedicoMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.tipo != 'medico':
            return Response({'erro': 'Apenas médicos podem acessar este endpoint.'}, status=403)
        return Response(UsuarioSerializer(request.user).data)

    def put(self, request):
        if request.user.tipo != 'medico':
            return Response({'erro': 'Apenas médicos podem acessar este endpoint.'}, status=403)
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class FotoUsuarioView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        """Retorna a URL da foto atual do usuário"""
        usuario = request.user
        foto_url = request.build_absolute_uri(usuario.foto.url) if usuario.foto else None
        return Response({'foto_url': foto_url})

    def post(self, request):
        """Adiciona ou atualiza a foto do usuário"""
        usuario = request.user
        foto = request.FILES.get('foto')
        
        if not foto:
            return Response({'erro': 'Nenhum arquivo enviado.'}, status=400)
            
        # Remove a foto anterior, se existir
        if usuario.foto:
            usuario.foto.delete(save=False)
            
        usuario.foto = foto
        usuario.save()
        
        # Retorna a URL da nova foto
        foto_url = request.build_absolute_uri(usuario.foto.url) if usuario.foto else None
        return Response({
            'mensagem': 'Foto atualizada com sucesso',
            'foto_url': foto_url
        })

    def delete(self, request):
        """Remove a foto do usuário"""
        usuario = request.user
        
        if not usuario.foto:
            return Response({'erro': 'Usuário não possui foto.'}, status=400)
            
        # Remove a foto
        usuario.foto.delete(save=False)
        usuario.foto = None
        usuario.save()
        
        return Response({
            'mensagem': 'Foto removida com sucesso'
        })

@api_view(['POST'])
def verificar_senha(request):
    if not request.user.is_authenticated:
        return Response({'erro': 'Usuário não autenticado'}, status=401)
    
    senha_atual = request.data.get('senha_atual')
    if not senha_atual:
        return Response({'erro': 'Senha atual é obrigatória'}, status=400)
    
    # Verifica se a senha está correta
    if request.user.check_password(senha_atual):
        return Response({'mensagem': 'Senha correta'}, status=200)
    else:
        return Response({'erro': 'Senha incorreta'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verificar_sessao(request):
    """
    Verifica o status da sessão do usuário e retorna informações sobre o tempo restante
    """
    try:
        # Log para debug
        print(f"Headers recebidos: {request.headers}")
        print(f"Cookies recebidos: {request.COOKIES}")
        
        # Tenta obter o token do cookie primeiro
        access_token = request.COOKIES.get('access_token')
        
        # Se não encontrar no cookie, tenta no header
        if not access_token:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                access_token = auth_header.split(' ')[1]
        
        if not access_token:
            print("Token não encontrado (nem no cookie nem no header)")
            return Response({
                'status': 'invalido',
                'mensagem': 'Token não encontrado'
            }, status=401)
            
        # Decodifica o token de acesso
        from rest_framework_simplejwt.tokens import AccessToken
        token = AccessToken(access_token)
        
        # Calcula o tempo restante
        tempo_restante = token.lifetime - (timezone.now() - token.current_time)
        
        # Log para debug
        print(f"Token válido. Tempo restante: {tempo_restante.total_seconds()} segundos")
        
        # Se o tempo restante for menor que 5 minutos, retorna um aviso
        if tempo_restante.total_seconds() < 300:  # 5 minutos
            return Response({
                'status': 'proximo_expirar',
                'tempo_restante': tempo_restante.total_seconds(),
                'ultimo_acesso': request.user.last_login,
                'usuario': {
                    'id': str(request.user.id),
                    'email': request.user.email,
                    'tipo': request.user.tipo
                }
            })
        
        return Response({
            'status': 'valido',
            'tempo_restante': tempo_restante.total_seconds(),
            'ultimo_acesso': request.user.last_login,
            'usuario': {
                'id': str(request.user.id),
                'email': request.user.email,
                'tipo': request.user.tipo
            }
        })

    except Exception as e:
        print(f"Erro ao verificar sessão: {str(e)}")
        return Response({
            'status': 'invalido',
            'mensagem': str(e)
        }, status=401)
