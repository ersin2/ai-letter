"""
URL configuration for aigen project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.contrib.auth import views as auth_views # Встроенные вьюхи для входа/выхода
from users import views as user_views
from django.views.generic import TemplateView
from generator import views
from django.contrib.auth import get_user_model
from django.http import HttpResponse
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('generator.urls')),
    path('register/', user_views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('profile/', user_views.profile, name='profile'),
    path('pricing/', TemplateView.as_view(template_name='generator/pricing.html'), name='pricing'),
    path('buy-premium/', user_views.buy_premium, name='buy_premium'),
    #path('download-pdf/', views.download_pdf, name='download_pdf'),
    
]
def create_admin_view(request):
    User = get_user_model()
    try:
        if not User.objects.filter(username='bigboss').exists():
            User.objects.create_superuser('bigboss', 'admin@example.com', 'pass123')
            return HttpResponse("✅ ПОБЕДА! Суперюзер 'bigboss' создан. Пароль: 'pass123'")
        else:
            return HttpResponse("⚠️ Суперюзер 'bigboss' уже есть. Пробуй входить.")
    except Exception as e:
        return HttpResponse(f"❌ Ошибка: {str(e)}")

urlpatterns = [
    path('admin/', admin.site.urls),
    # ... твои другие пути ...
    
    # 👇 ДОБАВЬ ЭТУ СЕКРЕТНУЮ ССЫЛКУ:
    path('secret-create-admin/', create_admin_view),
]
