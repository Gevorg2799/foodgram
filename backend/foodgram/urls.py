"""Обработка путей приложаения."""

from api.views import ShortLinkRedirectView
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('api/', include('api.urls')),
    path('s/<str:short_code>/', ShortLinkRedirectView.as_view(),
         name='short-link-redirect'),
    path('admin/', admin.site.urls)

]
