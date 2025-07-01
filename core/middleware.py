from django.utils.deprecation import MiddlewareMixin

class ActivityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Aqui você pode adicionar lógica para rastrear atividade do usuário
        pass

    def process_response(self, request, response):
        # Aqui você pode adicionar lógica para processar a resposta
        return response 