#Needed variables in addition to the standard Django settings. 

#CAS oauth vars
OAUTH_URL = "" #CAS oauth endpoint
CLIENTID = "" #CAS client id
CLIENT_SECRET = "" #CAS secret key
#other
CSRF_TRUSTED_ORIGINS = ["https://yoursite.instructure.com/"] #the url of LMS you will be using
#Application definition
INSTALLED_APPS = [
  ...
    'myauth.apps.MyauthConfig',
    'lti.apps.LtiConfig',
]
ROOT_URLCONF = 'tusker.urls'
SESSION_COOKIE_SAMESITE = None
CSRF_COOKIE_SAMESITE = None

LOGIN_URL = "set to your base url + /auth/"

#Middleware 
#Note that XFrameOptionsMiddleware and CsrfViewMiddleware are not used
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
#    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
