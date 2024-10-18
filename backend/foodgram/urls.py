"""Обработка путей приложаения."""

from django.contrib import admin
from django.urls import include, path
from recipes.views import ShortLinkRedirectView

urlpatterns = [
    path('api/', include('api.urls')),
    path('s/<str:short_code>/', ShortLinkRedirectView.as_view(),
         name='short-link-redirect'),
    path('admin/', admin.site.urls)

]
