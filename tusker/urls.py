"""tusker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.contrib.auth.decorators import login_required
from django.conf.urls import url, include
from django.contrib import admin
from django.http import HttpResponse
from lti.views import LaunchView, ltilogin, JwksView, TestView, dashboardView,courseView
import os
import tusker.settings
from django.conf import settings
from django.urls import path
urlpatterns = [
    path('admin/', admin.site.urls),
	path('ltilogin/', ltilogin),
	path('launch/', LaunchView.as_view()),
	path('jwks/', JwksView.as_view()),
	path('test/', TestView.as_view()),
	path('dashboard/<int:cid>/', login_required(courseView.as_view())),
	path('dashboard/', login_required(dashboardView.as_view()), name="dashboard"),
	path("auth/", include("myauth.urls")),

]
