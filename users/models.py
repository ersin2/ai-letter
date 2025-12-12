from django.db import models
from django.contrib.auth.models import User

# 👇 Вот он, этот класс, который Django не может найти
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    generations_count = models.IntegerField(default=3) # Даем 3 попытки
    is_premium = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} Profile'