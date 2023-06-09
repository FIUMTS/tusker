from myauth.views import authorizeView, tokenView, logoutView
from django.urls import path


urlpatterns = [
	path("", authorizeView.as_view(), name="startlogin"),
	path("token", tokenView.as_view()),
	path("logout/", logoutView.as_view(),name="logout"),
]
