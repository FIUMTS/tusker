from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class course(models.Model):
	coursecontext = models.CharField(max_length=90)
	coursename = models.CharField(max_length=150)

	def __str__(self):
		return self.coursename + " " + self.coursecontext

class courseUsers(models.Model):
	userid = models.ForeignKey(User, on_delete=models.CASCADE)
	courseid = models.ForeignKey(course, on_delete=models.CASCADE)
	role = models.CharField(max_length=30)

	def __str__(self):
		return self.userid.username + "'s course: " + self.courseid.coursename
	class Meta:
		verbose_name_plural = "Course Users"

class ltiapp(models.Model):
	courseid = models.ForeignKey(course, on_delete=models.CASCADE)
	header = models.TextField()
	body = models.TextField()

	def __str__(self):
		return self.courseid.coursename + " " + self.courseid.coursecontext
