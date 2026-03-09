"""
URL configuration for comet project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("people/", include("apps.people.urls")),  # Includes all ACCC app URLs
    path("classrooms/", include("apps.classrooms.urls")),  # Includes all ACCC app URLs
    # path("operations/", include("apps.operations.urls")),  # Includes all ACCC app URLs
    path("planning/", include("apps.planning.urls")),  # Includes all ACCC app URLs
    # path('', RedirectView.as_view(url='/accc/rooms/current', permanent=True)),
]
urlpatterns += [
    path('accounts/', include('django.contrib.auth.urls')),
]