from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from virtmgr.model.models import *

def index(request):

   	if not request.user.is_authenticated():
	   	return HttpResponseRedirect('/')

	usr_id = request.user.id
	usr_name = request.user
	hosts = Host.objects.filter(user=usr_id)
	kvm_host = []

	for host in hosts:
		kvm_host.append(host.hostname)
	
	return render_to_response('hosts.html', locals())