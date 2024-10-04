from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q

MAX_LENGTH = 150


class MyUser(AbstractUser):
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH,
        blank=False,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH,
        blank=False,
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=MAX_LENGTH,
        blank=False,
        unique=True
    )
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=254,
        blank=False,
        unique=True
    )

    top_recipes = models.TextField(
        'Топ любимых блюд',
        max_length=500,
        blank=True,
        help_text='Перечислите свои любимые блюда'

    )
    avatar = models.ImageField(
        'Аватар',
        blank=True, null=True,
        upload_to='users/images/',
        help_text='загрузите вашу аватарку'
    )
    # USERNAME_FIELD = 'username'
    # EMAIL_FIELD = 'email'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-date_joined',)

    def __str__(self):
        return self.get_full_name()


class SubscrUser(models.Model):
    subscriber = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('subscriber',)
        constraints = [
            models.UniqueConstraint(
                name='Unique_subscrib',
                fields=('subscriber', 'author')),
            models.CheckConstraint(
                check=~Q(author=F("subscriber")),
                name="Нельзя подписаться на себя"
            ),
        ]

    def __str__(self):
        return f'{self.subscriber} подписан на {self.author}'
