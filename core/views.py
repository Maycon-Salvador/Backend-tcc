from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from django.core.management import call_command
# View de login com JWT
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# 🧩 View para envio de código por e-mail
import random
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["POST"])
def enviar_codigo_verificacao(request):
    email = request.data.get("email")

    if not email:
        return Response({"erro": "E-mail é obrigatório."}, status=400)

    codigo = str(random.randint(100000, 999999))
    cache.set(f"verificacao_{email}", codigo, timeout=300)  # código vale por 5 minutos

    send_mail(
        subject="Código de Verificação - MedAgenda",
        message=f"Seu código de verificação é: {codigo}",
        from_email="no-reply@medagenda.com",
        recipient_list=[email],
    )

    return Response({"mensagem": "Código enviado com sucesso para o e-mail."})
@api_view(["POST"])
def verificar_codigo(request):
    email = request.data.get("email")
    codigo_recebido = request.data.get("codigo")

    if not email or not codigo_recebido:
        return Response({"erro": "E-mail e código são obrigatórios."}, status=400)

    codigo_salvo = cache.get(f"verificacao_{email}")

    if codigo_salvo == codigo_recebido:
        return Response({"mensagem": "Código verificado com sucesso."})
    else:
        return Response({"erro": "Código inválido ou expirado."}, status=400)

@api_view(["GET"])
def rodar_migracoes(request):
    try:
        call_command("migrate")
        return Response({"mensagem": "Migrações aplicadas com sucesso."})
    except Exception as e:
        return Response({"erro": str(e)}, status=500)