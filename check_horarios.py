import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MedAgenda.settings')
django.setup()

from core.models import Usuario, HorarioAtendimento

# Lista todos os médicos
print("\nMédicos cadastrados:")
for medico in Usuario.objects.filter(tipo='medico'):
    print(f"\nMédico: {medico.email} (ID: {medico.id})")
    horarios = HorarioAtendimento.objects.filter(medico=medico)
    print(f"Total de horários: {horarios.count()}")
    for h in horarios:
        print(f"- {h.dia_semana}: {h.horarios}") 