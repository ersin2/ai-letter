from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'users/register.html', {'form': form})
# Create your views here.
@login_required
def profile(request):
    return render(request, 'users/profile.html')
# ... твои импорты

@login_required
def buy_premium(request):
    # Получаем профиль
    profile = request.user.profile
    
    # Включаем Премиум
    profile.is_premium = True
    profile.save()
    
    # Возвращаем пользователя в профиль, чтобы он увидел результат
    return redirect('profile')