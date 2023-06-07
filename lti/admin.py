from django.contrib import admin
from lti.models import courseUsers, course, ltiapp
# Register your models here.

admin.site.register(courseUsers, admin.ModelAdmin)
admin.site.register(course, admin.ModelAdmin)
admin.site.register(ltiapp, admin.ModelAdmin)
