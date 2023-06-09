from django.conf import settings

def getBaseUrl(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {"HOME_URL": settings.HOME_URL}
