from django.contrib import admin
from core.views_auth import LoginComCookieView
from django.urls import path, include
from core.views_google import google_redirect
from rest_framework_simplejwt.views import (
    
    TokenRefreshView,
)

urlpatterns = [
    path('api/token/', LoginComCookieView.as_view(), name='token_obtain_pair'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),  # <-- esse inclui as rotas do seu app core
    
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
