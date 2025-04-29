import os
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt
from google_auth_oauthlib.flow import Flow
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from googleapiclient.discovery import build
from core.models import Usuario


# 🔗 LOGIN COM GOOGLE
@api_view(['GET'])
@permission_classes([AllowAny])
def google_login(request):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Apenas para ambiente local (HTTP)

    flow = Flow.from_client_secrets_file(
        'google_credentials/client_secret.json',
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    # 🔐 Pega o usuário da sessão OU via query param (caso navegador não esteja autenticado)
    usuario_id = request.GET.get('usuario_id') or (request.user.id if request.user.is_authenticated else None)
    if usuario_id:
        request.session['usuario_id'] = usuario_id
        print("✅ ID do usuário salvo na sessão:", usuario_id)
    else:
        print("⚠️ Nenhum ID de usuário encontrado (nem na sessão nem via query param)")

    request.session['oauth_state'] = state
    return HttpResponseRedirect(authorization_url)


# 🔁 CALLBACK DO GOOGLE
@csrf_exempt
def google_redirect(request):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    try:
        flow = Flow.from_client_secrets_file(
            'google_credentials/client_secret.json',
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )

        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials

        print("✅ Token recebido:", credentials.token)

        usuario_id = request.session.get('usuario_id')

        if usuario_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            usuario = User.objects.get(id=usuario_id)

            print("✅ Salvando token no usuário:", usuario.username)
            usuario.google_access_token = credentials.token
            usuario.google_refresh_token = credentials.refresh_token
            usuario.google_token_expiry = make_aware(credentials.expiry)
            usuario.save()
        else:
            print("⚠️ Nenhum usuário encontrado na sessão.")

        return JsonResponse({
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'expires_in': credentials.expiry.isoformat(),
            'mensagem': 'Token recebido com sucesso'
        })

    except Exception as e:
        print("❌ Erro ao trocar code por token:", e)
        return JsonResponse({'erro': str(e)}, status=400)


# 📅 CRIAÇÃO DO EVENTO NA AGENDA GOOGLE
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def criar_evento_google(request):
    user = request.user
    print("Usuário autenticado?", user.is_authenticated)
    print("Access Token salvo:", user.google_access_token)
    print("Dados recebidos:", request.data)

    access_token = user.google_access_token
    refresh_token = user.google_refresh_token
    titulo = request.data.get('titulo')
    descricao = request.data.get('descricao', '')
    inicio = request.data.get('inicio')
    fim = request.data.get('fim')

    if not access_token or not titulo or not inicio or not fim:
        return Response({'erro': 'Campos obrigatórios: titulo, inicio, fim (e token salvo)'}, status=400)

    try:
        from google.oauth2.credentials import Credentials
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )

        calendar_service = build('calendar', 'v3', credentials=creds)

        event = {
            'summary': titulo,
            'description': descricao,
            'start': {
                'dateTime': inicio,
                'timeZone': 'America/Campo_Grande',
            },
            'end': {
                'dateTime': fim,
                'timeZone': 'America/Campo_Grande',
            },
        }

        event = calendar_service.events().insert(calendarId='primary', body=event).execute()
        return Response({'mensagem': 'Evento criado com sucesso!', 'evento_id': event['id']})

    except Exception as e:
        return Response({'erro': str(e)}, status=500)
