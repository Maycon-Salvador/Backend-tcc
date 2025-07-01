# MedAgenda - Backend

Backend do sistema MedAgenda, uma plataforma de agendamento de consultas médicas desenvolvida com Django e Django REST Framework.

## 🚀 Funcionalidades

- **Autenticação e Usuários**

  - Registro de usuários (pacientes e médicos)
  - Login com JWT (JSON Web Tokens)
  - Recuperação de senha
  - Validação de CPF e email
  - Upload de foto de perfil
  - Diferentes tipos de usuário (médico e comum)

- **Agendamentos**

  - Criação de agendamentos
  - Confirmação/cancelamento de consultas
  - Listagem de agendamentos por usuário
  - Diferentes status de agendamento (solicitado, agendado, cancelado)
  - Notificações por email
  - Upload de anexos (exames, documentos)

- **Horários de Atendimento**

  - Cadastro de horários pelos médicos
  - Definição de duração e intervalo entre consultas
  - Marcação de indisponibilidade
  - Validação de horários disponíveis

## 🛠️ Tecnologias

- Python 3.8+
- Django 4.2+
- Django REST Framework
- PostgreSQL
- JWT Authentication
- Celery (para tarefas assíncronas)

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- PostgreSQL

## 🔧 Instalação

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/medagenda-backend.git
cd medagenda-backend
```

2. Crie e ative um ambiente virtual:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:

```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. Execute as migrações:

```bash
python manage.py migrate
```

6. Crie um superusuário:

```bash
python manage.py createsuperuser
```

7. Inicie o servidor:

```bash
python manage.py runserver
```

## 📝 Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
DEBUG=True
SECRET_KEY=sua_chave_secreta
DATABASE_URL=postgresql://usuario:senha@localhost:5432/medagenda
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha
```

## 🧪 Testes

O projeto inclui uma suite de testes abrangente que cobre:

- Autenticação e registro de usuários
- Criação e gerenciamento de horários de atendimento
- Criação e gerenciamento de agendamentos
- Validações de permissões
- Casos de erro e exceções

Execute os testes com:

```bash
python manage.py test core
```

## 📚 Documentação da API

### Autenticação

- `POST /api/token/` - Login (obter token JWT)
- `POST /api/token/refresh/` - Renovar token JWT
- `POST /register/` - Registro de usuário
- `POST /enviar-codigo/` - Enviar código de verificação
- `POST /verificar-codigo/` - Verificar código

### Agendamentos

- `GET /meus-agendamentos/` - Listar agendamentos
- `POST /agendamentos/` - Criar agendamento
- `POST /agendamentos/{id}/aceitar/` - Aceitar agendamento
- `POST /agendamentos/{id}/cancelar/` - Cancelar agendamento
- `PATCH /agendamentos/{id}/status/` - Atualizar status

### Horários de Atendimento

- `GET /horarios-atendimento/` - Listar horários
- `POST /horarios-atendimento/` - Criar horário
- `PATCH /horarios-atendimento/{id}/` - Atualizar horário
- `DELETE /horarios-atendimento/{id}/` - Deletar horário

### Médicos

- `GET /medicos/` - Listar médicos
- `GET /medico/me/` - Dados do médico logado

## 🔒 Segurança

- Autenticação JWT para todas as rotas protegidas
- Validação de CPF e email no registro
- Verificação de permissões por tipo de usuário (médico/comum)
- Proteção contra agendamentos duplicados
- Validação de horários disponíveis

## 📱 Integração com Frontend

O backend foi desenvolvido para se integrar com o frontend do MedAgenda, fornecendo:

- API RESTful completa
- Endpoints para todas as funcionalidades necessárias
- Respostas em formato JSON
- Tratamento de erros padronizado
- Documentação clara dos endpoints

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request
