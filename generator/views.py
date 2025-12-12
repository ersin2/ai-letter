import httpx
import os
from django.shortcuts import render, redirect
from dotenv import load_dotenv
from django.contrib.auth.decorators import login_required
from users.models import Profile  # Импорт модели профиля

load_dotenv()

@login_required(login_url='login') 
def home(request):
    result = None
    error_message = None
    
    # 1. Получаем или создаем профиль (защита от ошибок)
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Если профиль новый, даем 3 попытки
    if created:
        profile.generations_count = 3
        profile.save()

    if request.method == "POST":
        
        # 2. Проверяем лимиты
        if profile.generations_count > 0 or profile.is_premium:
            
            resume_text = request.POST.get('resume')
            job_description = request.POST.get('job_description')
            api_key = os.getenv("GROQ_API_KEY") # <--- БЕРЕМ КЛЮЧ ИЗ ENV (БЕЗОПАСНО)

            if not api_key:
                 error_message = "Ошибка сервера: API ключ не найден."
            else:
                magic_prompt = f"""
                Role: Expert HR. Write a Cover Letter.
                RESUME: {resume_text}
                JOB: {job_description}
                Output ONLY the letter body.
                """

                try:
                    # Настройки заголовков (Здесь раньше была ошибка)
                    headers = {
                        "Authorization": f"Bearer {api_key}", # Используем переменную, а не текст
                        "Content-Type": "application/json"
                    }
                    
                    data = {
                        "model": "llama3-8b-8192", 
                        "messages": [
                            {"role": "system", "content": "You are a professional CV writer."},
                            {"role": "user", "content": magic_prompt}
                        ],
                        "temperature": 0.7
                    }

                    response = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=30.0)
                    
                    if response.status_code == 200:
                        result = response.json()['choices'][0]['message']['content']
                        
                        # Списываем попытку (если не премиум)
                        if not profile.is_premium:
                            profile.generations_count -= 1
                            profile.save()
                            
                    else:
                        error_message = f"Ошибка API: {response.text}"

                except Exception as e:
                    error_message = f"Ошибка соединения: {str(e)}"
        
        else:
            # Лимиты кончились
            error_message = "У вас закончились бесплатные попытки! 😢 Оформите подписку."

    return render(request, 'generator/home.html', {
        'result': result, 
        'error_message': error_message
    })