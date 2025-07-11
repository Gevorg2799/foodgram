"""Работа с моделями в админке."""

from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from .models import SubscrUser

User = get_user_model()


@admin.register(User)
class AdminUser(UserAdmin):
    """Отображение и редактирование пользователей в админке."""

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_superuser',
        'date_joined',
        'avatar',
    )
    list_filter = ('is_staff', 'is_superuser',)
    search_fields = ('username', 'email', 'first_name', 'last_name',)
    list_display_links = ('username',)
    list_editable = (
        'is_staff',
        'is_superuser',
    )
    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('date_joined', 'last_login')
    date_hierarchy = 'date_joined'


@admin.register(SubscrUser)
class AdminSubscrUser(admin.ModelAdmin):
    """Отображенеи подписок."""

    list_display = ('id', 'subscriber', 'author')
    search_fields = ('subscriber', 'author')

    def save_model(self, request, obj, form, change):
        """Работа с подпиской."""
        if obj.subscriber == obj.author:
            raise ValidationError("Вы не можете подписаться на самого себя.")
        super().save_model(request, obj, form, change)


admin.site.unregister(Group)
