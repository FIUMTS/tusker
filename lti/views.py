from django.shortcuts import render
from django.conf import settings
from django.views import View
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseNotFound
from pylti1p3.contrib.django import DjangoOIDCLogin, DjangoMessageLaunch, DjangoCacheDataStorage
from pylti1p3.deep_link_resource import DeepLinkResource
from pylti1p3.grade import Grade
from pylti1p3.lineitem import LineItem
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.registration import Registration
import os
import logging
from django.contrib.auth.models import User
from django.contrib.auth import  login
from django.contrib.auth.models import Group
from lti.models import courseUsers, course, ltiapp
from django.core.exceptions import ObjectDoesNotExist
logger = logging.getLogger("django")

# Create your views here.
class ExtendedDjangoMessageLaunch(DjangoMessageLaunch):

    def validate_nonce(self):
        """
        Probably it is bug on "https://lti-ri.imsglobal.org":
        site passes invalid "nonce" value during deep links launch.
        Because of this in case of iss == http://imsglobal.org just skip nonce validation.
		skipping in canvas beta for now. not matching. no clue why.... 
        """
        #return self
        iss = self.get_iss()
        deep_link_launch = self.is_deep_link_launch()
        if iss == "http://imsglobal.org" and deep_link_launch:
            return self
        return super().validate_nonce()

def get_launch_url(request):
    target_link_uri = request.POST.get('target_link_uri', request.GET.get('target_link_uri'))
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')
    return target_link_uri


def get_tool_conf():
    tool_conf = ToolConfJsonFile(os.path.join(settings.BASE_DIR, 'config', 'lti.json'))

    return tool_conf

def get_launch_url(request):
    target_link_uri = request.POST.get('target_link_uri', request.GET.get('target_link_uri'))
    logger.debug("get launch")
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')
    return target_link_uri

def isAdmin(user):
	if user.is_superuser:
		return True
	if user.groups.filter(name="admin").exists():
		return True
	
	return False


def ltilogin(request):
	tool_conf = get_tool_conf()
	launch_data_storage = DjangoCacheDataStorage()

	oidc_login = DjangoOIDCLogin(request, tool_conf, launch_data_storage=launch_data_storage)
	target_link_uri = get_launch_url(request)
	logger.debug("log in view")
	return oidc_login\
		.enable_check_cookies()\
		.redirect(target_link_uri)

def getPermissions(lmsroles):
	r = []
	admingroup, created = Group.objects.get_or_create(name='admin')
	teachergroup, created = Group.objects.get_or_create(name='instructor')


	for role in lmsroles:
		if "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator" in role:
			r.append(admingroup)
		if "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Instructor" in role:
			r.append(teachergroup)

	return r

class LaunchView(View):
	def post(self,request):
		tool_conf = get_tool_conf()
		launch_data_storage = DjangoCacheDataStorage()
		message_launch = ExtendedDjangoMessageLaunch(request, tool_conf, launch_data_storage=launch_data_storage)
		message_launch_data = message_launch.get_launch_data()
		role = ""

		logger.debug("log in view ")
		logger.debug(message_launch_data)
		if message_launch.has_nrps():
			email = message_launch_data.get('email', '')
			fname = message_launch_data.get('given_name', '')
			lname = message_launch_data.get('family_name', '')
			courseinfo = message_launch_data.get("https://purl.imsglobal.org/spec/lti/claim/resource_link",'')
			courseid = courseinfo["id"]
			coursename = courseinfo["title"]
			try:
				user = User.objects.get(username=email)
				groups = getPermissions(message_launch_data["https://purl.imsglobal.org/spec/lti/claim/roles"])
				for group in groups:
					logger.debug("Group:" + group.name)
					if group not in user.groups.all():
						user.groups.add(group)
				user.save()
			except User.DoesNotExist:
				logger.debug("Creating User %s"%(email))
				user = User.objects.create_user(email,email,"some#random#1")
				user.first_name = fname
				user.last_name = lname
				user.save()
				user.groups.set(getPermissions(message_launch_data["https://purl.imsglobal.org/spec/lti/claim/roles"]))
				user.save()
			tempcourse = course.objects.filter(coursecontext = courseid)

			if len(tempcourse) == 0:
				mycourse = course(coursecontext = courseid,coursename = coursename)
				mycourse.save()
			else:
				mycourse = tempcourse[0]

			try:
				app = ltiapp.objects.get(courseid=mycourse)
			except:
				app = []
			 

			if user.groups.filter(name="instructor").exists():
				role = "instructor"
			else:
				role = "user"
 
			try:
				coursemodel = courseUsers.objects.get(userid=user, 
				courseid=mycourse, role=role)
			except:
				coursemodel = courseUsers(userid=user, courseid=mycourse,
				role=role)
				coursemodel.save()

			login(request, user)
			
			if len(app) == 0:
				return render(request, "landing.html")

			return HttpResponse("Hello %s"%(message_launch_data.get('given_name', '')))
		else:
			return HttpResponse("Hi, no nrps enabled.")

class JwksView(View):
	def get(self,request):
		tool_conf = get_tool_conf()
		return JsonResponse(tool_conf.get_jwks(), safe=False)




class dashboardView(View):
	def get(self,request):
		admin = False

		if isAdmin(request.user):
			courses = course.objects.all()
			isadmin = True
			logger.debug("Is an admin")
		else:
			courses = courseUsers.objects.filter(userid=request.user, role = "instructor")

		return render(request, "dashboard.html",{"courses": courses, "admin": isadmin})


class TestView(View):
	def get(self,request):
		logger.debug("TEST")
		return HttpResponse("hi")
