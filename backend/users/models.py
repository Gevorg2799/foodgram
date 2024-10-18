"""Работа с моделями в приложении."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.validators import UnicodeUsernameValidator
# from django.core.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

MAX_LENGTH = 150


class User(AbstractUser):
    """Моедль пользователя."""

    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH,
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=MAX_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator()],
    )
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=254,
        unique=True
    )
    avatar = models.ImageField(
        'Аватар',
        blank=True, null=True,
        upload_to='users/images/',
        help_text='загрузите вашу аватарку'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password', 'first_name', 'last_name']

    class Meta:
        """Свойства."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-username',)

    def __str__(self):
        """Отображение модели."""
        return self.get_full_name()


class SubscrUser(models.Model):
    """Модель для подписки на пользователей."""

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор'
    )

    class Meta:
        """Свойства."""

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('subscriber',)
        constraints = [
            models.UniqueConstraint(
                name='Unique_subscrib',
                fields=('subscriber', 'author')),
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F('author')),
                name='self_subscription'
            ),
        ]

    def clean(self):
        """Проверка подписки на самого себя перед сохранением."""
        if self.subscriber == self.author:
            raise ValidationError('Вы не можете подписаться на самого себя.')

    def save(self, *args, **kwargs):
        """Проверка перед сохранением."""
        self.clean()  # Вызов метода clean() перед сохранением
        super().save(*args, **kwargs)

    def __str__(self):
        """Отображение модели."""
        return f'{self.subscriber} подписан на {self.author}'
