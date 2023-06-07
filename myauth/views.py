from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.conf import settings
import requests
import json
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from lti.models import course, courseUsers
from django.contrib.auth import login
from django.urls import reverse

endpoint = [
		"cas/oauth2.0/authorize",
		"cas/oauth2.0/accessToken",
		"cas/oauth2.0/profile",
	]


# Create your views here.
class authorizeView(View):

	def get(self,request):
		#check if user is logged in and if the token is expired
		return redirect("%s/%s?response_type=code&client_id=%s&redirect_uri=https://mtsupload.fiu.edu/lti/auth/token"%
			(settings.OAUTH_URL,endpoint[0], settings.CLIENTID))

class tokenView(View):
	
	def get(self, request):
		#redirect if user is logged in 
		#if there is no code parameter, throw an error
		try:
			code = request.GET["code"]
		except:
			return HttpResponseBadRequest("Invalid")
			
		r = requests.post("%s/%s"%(settings.OAUTH_URL, endpoint[1]), data= {"grant_type":"authorization_code","client_id": settings.CLIENTID, "code": request.GET["code"],"client_secret": settings.CLIENT_SECRET, "redirect_uri": "https://mtsupload.fiu.edu"})
		
		#if we didn't get back a access token from CAS, kill it
		if r.status_code != 200 and r.status_code != 302:
			return HttpResponseBadRequest("Invalid request")

		creds = json.loads(r.text)

		r = requests.get("%s/%s?access_token=%s"%(settings.OAUTH_URL, endpoint[2], creds["access_token"]))	

		if r.status_code != 200 and r.status_code != 302:
			return HttpResponseBadRequest("Invalid second request")
        
		userdata = json.loads(r.text)

		expire = datetime.fromtimestamp(userdata["attributes"]["authenticationDate"])
		expire = expire + timedelta(seconds=creds["expires_in"])
		name = userdata['attributes']['name']
		email = userdata['attributes']['email']
		try:
			myuser = User.objects.get(username=email)
		except:
			myuser = User.objects.create_user(email,email,userdata["attributes"]["oauthClientId"])
			names = name.split()
			if len(names) > 1:
				myuser.first_name = names[0]
				myuser.last_name = names[1]
			else:
				myuser.first_name = name

			myuser.save()
			
		login(request, myuser)

		request.session['email'] = email
		request.session['name'] = name
		return redirect(reverse("dashboard"))
		#return render(request,"dashboard.html", {"courses": []})

