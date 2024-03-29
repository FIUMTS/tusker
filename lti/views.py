from django.shortcuts import render
from django.conf import settings
from django.views import View
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseNotFound
from pylti1p3.contrib.django import DjangoOIDCLogin, DjangoMessageLaunch, DjangoCacheDataStorage
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from pylti1p3.deep_link_resource import DeepLinkResource
from pylti1p3.grade import Grade
from pylti1p3.lineitem import LineItem
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.registration import Registration
import os
import logging
import random
import string
from django.contrib.auth.models import User
from django.contrib.auth import  login
from django.contrib.auth.models import Group
from lti.models import courseUsers, course, ltiapp
from django.core.exceptions import ObjectDoesNotExist
from lti.forms import appForm
from django.core.paginator import Paginator
import json
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
	if user.groups.filter(name = "admin").exists():
		return True	
	return False

def hasAccess(user, course):
	userdata = courseUsers.objects.filter(courseid=course, userid=user)	
	
	if not isAdmin(user) and userdata.count() == 0:
            return False
	return True

def ltilogin(request):
	tool_conf = get_tool_conf()
	launch_data_storage = DjangoCacheDataStorage(cache_name='default')

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

	def post(self, request):
		tool_conf = get_tool_conf()
		launch_data_storage = DjangoCacheDataStorage(cache_name='default')
		message_launch = ExtendedDjangoMessageLaunch(request, tool_conf,
													launch_data_storage = launch_data_storage)
		message_launch_data = message_launch.get_launch_data()
		role = ""
		launchid = message_launch.get_launch_id()
		request.session["launch"] = launchid

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
				user = User.objects.create_user(email, email, "some#random#1")
				user.first_name = fname
				user.last_name = lname
				user.save()
				user.groups.set(getPermissions(message_launch_data["https://purl.imsglobal.org/spec/lti/claim/roles"]))
				user.save()
			tempcourse = course.objects.filter(coursecontext = courseid)

			if tempcourse.count() == 0:
				mycourse = course(coursecontext = courseid, coursename = coursename)
				mycourse.save()
			else:
				mycourse = tempcourse[0]


			if user.groups.filter(name = "instructor").exists():
				role = "instructor"
			else:
				role = "user"
 
			try:
				coursemodel = courseUsers.objects.get(userid = user, 
													courseid = mycourse,
													role = role)
			except:
				coursemodel = courseUsers(userid = user, courseid = mycourse,
				role = role)
				coursemodel.save()

			login(request, user)

			try:
				app = ltiapp.objects.get(courseid = mycourse)
			except:
				return render(request, "landing.html")

			if len(app.body) == 0 and len(app.header) == 0:
				return render(request, "landing.html")

			return render(request, "frame.html", {"body": app.body, "head": app.header})
		else:
			return HttpResponse("Hi, no nrps enabled.")


class JwksView(View):

	def get(self, request):
		tool_conf = get_tool_conf()
		return JsonResponse(tool_conf.get_jwks(), safe=False)


class dashboardView(View):


	@method_decorator(csrf_protect)
	def get(self, request):
		isadmin = False
		p = request.GET.get('p',1)

		if isAdmin(request.user):
			courses = course.objects.all()
			isadmin = True
			logger.debug("Is an admin")
		else:
			courses = courseUsers.objects.filter(userid=request.user, role = "instructor")

		page = Paginator(courses, 10)
		pagecourses = page.get_page(p)

		return render(request, "dashboard.html",{"courses": pagecourses, "admin": isadmin})

	@method_decorator(csrf_protect)
	def post(self, request):
		isadmin = False

		if isAdmin(request.user):
			isadmin = True
			courses = course.objects.filter(coursename__icontains = request.POST["sbox"])
		else:
			courses = courseUsers.objects.filter(userid = request.user,
												role = "instructor",
												courseid__coursename__contains = request.POST["sbox"])
		page = Paginator(courses, 10)
		pagecourses = page.get_page(1)

		return render(request, "dashboard.html",{"courses": pagecourses, "admin": isadmin})


class courseView(View):
	

	@method_decorator(csrf_protect)
	def get(self, request, cid):
		key = ''
		url = ''

		try:
			mycourse = course.objects.get(pk=cid)
		except course.DoesNotExist:
			return HttpResponseNotFound()

		if not hasAccess(request.user, mycourse):
			return HttpResponseNotFound()
		
		try:
			ltiinfo = ltiapp.objects.get(courseid=mycourse)
			body = ltiinfo.body
			header = ltiinfo.header

		except ltiapp.DoesNotExist:
			body = ''
			header = ''
			ltiinfo = ltiapp(courseid=mycourse,body=body,header=header)
			ltiinfo.save()
		
		f = appForm(initial={"body": body,"header": header})

		return render(request,"course.html", {"f": f, "course": mycourse})				

	@method_decorator(csrf_protect)
	def post(self, request, cid):
		msg = ''
	
		try:
			mycourse = course.objects.get(pk=cid)
		except course.DoesNotExist:
			return HttpResponseNotFound()

		if not hasAccess(request.user, mycourse):
			return HttpResponseNotFound()

		try:
			app = ltiapp.objects.get(courseid=mycourse)
		except ltiapp.DoesNotExist:
			return  HttpResponseNotFound()

		f = appForm(request.POST, initial={"body": app.body, "header": app.header})

		if f.is_valid():
			app.body = f.cleaned_data["body"]
			app.header = f.cleaned_data["header"]
			app.save()
			msg = "Saved!"
		else:
			msg = "Please check your input"

		return render(request,"course.html", {"f":f, "message": msg, "course": mycourse})
	

class FirstNameView(View):

	def get(self, request):
		logger.debug("First name")
		tool_conf = get_tool_conf()
		launch_data_storage = DjangoCacheDataStorage(cache_name='default')
		msg = ExtendedDjangoMessageLaunch.from_cache(request.session["launch"],\
			request, tool_conf, launch_data_storage=launch_data_storage)
		data = msg.get_launch_data()
		return HttpResponse(json.dumps({"name": data.get('given_name', '')}))

class FullNameView(View):

    def get(self, request):
        logger.debug("First name")
        tool_conf = get_tool_conf()
        launch_data_storage = DjangoCacheDataStorage(cache_name='default')
        msg = ExtendedDjangoMessageLaunch.from_cache(request.session["launch"],\
            request, tool_conf, launch_data_storage=launch_data_storage)
        data = msg.get_launch_data()
        return HttpResponse(json.dumps({"name": data.get('given_name', '') \
							+ " " + data.get('family_name', '')}))


class SUBView(View):


    def get(self, request):
        tool_conf = get_tool_conf()
        launch_data_storage = DjangoCacheDataStorage(cache_name='default')
        msg = ExtendedDjangoMessageLaunch.from_cache(request.session["launch"],\
            request, tool_conf, launch_data_storage=launch_data_storage)
        data = msg.get_launch_data()
        return HttpResponse(json.dumps({"sub": data.get('sub', '') }))


