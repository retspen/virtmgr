from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin    
from virtmgr.model.models import *

admin.site.unregister(Group)
admin.site.unregister(User)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff','is_active',)
    list_filter = ('is_staff', 'is_superuser', 'is_active',)    

class Hostadmin(admin.ModelAdmin):
    list_display = ('hostname', 'ipaddr', 'login', 'user')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Host, Hostadmin)
