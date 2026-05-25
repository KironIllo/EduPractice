"""
URL configuration for Investings project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path
from MainApp import views
from MainApp.modules import regi, logi, editi, profile, prices, notifi

from django.conf.urls.static import static
from .settings import STATIC_URL

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.Main, name='home'),
    path('signup/', regi.signup, name='signup'),
    path('login/', logi.login_view, name='login'),
    path('logout/', logi.logout_view, name='logout'),
    path('profile', profile.Profile, name='profile'),
    path('edit', editi.Edit, name='edit'),
    path('history', profile.History, name='history'),
] + static(STATIC_URL)