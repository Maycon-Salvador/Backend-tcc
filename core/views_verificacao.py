import random
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Esta função foi removida pois já existe uma implementação em views.py
# Use a função enviar_codigo de views.py em seu lugar
