from django.db import models
from django.contrib.auth.models import User

class Host(models.Model):
    hostname = models.CharField(max_length=20)
    ipaddr = models.CharField(max_length=16)
    login = models.CharField(max_length=20)
    passwd = models.CharField(max_length=20)
    user = models.ForeignKey(User)

    def __unicode__(self):
        return self.hostname