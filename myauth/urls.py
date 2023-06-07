from myauth.views import authorizeView, tokenView
from django.urls import path


urlpatterns = [
	path("", authorizeView.as_view(), name="startlogin"),
	path("token", tokenView.as_view()),
]
