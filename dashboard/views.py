import libvirt
import socket
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from virtmgr.model.models import *

def index(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login')

	usr_id = request.user.id
	usr_name = request.user
	
	def get_hosts_status():
		usr_id = request.user.id
		kvm_host = Host.objects.filter(user=usr_id)
		name_ipddr = {}
		for host in kvm_host:
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.settimeout(1)
				s.connect((host.ipaddr, 16509))
				s.close()
				status = 1
			except:
				status = 2
			name_ipddr[host.hostname] = (host.id, host.ipaddr, host.login, host.passwd, status)
	   	return name_ipddr
	
	def del_host(host):
		usr_id = request.user.id
		hosts = Host.objects.get(user=usr_id, hostname=host)
		hosts.delete()

	def add_host(host, ip, usr, passw):
		hostname = Host.objects.filter(user=usr_id, hostname=host)
		ipaddr = Host.objects.filter(user=usr_id, ipaddr=ip)
		if len(hostname) == 0 and len(ipaddr) == 0:
			if len(host) != 0 and len(ip) != 0 and len(usr) != 0 and len(passw) != 0:
				hosts = Host(user_id=usr_id, hostname=host, ipaddr=ip, login=usr, passwd=passw)
				hosts.save()

	def get_host_status(hosts):
		for host, info in hosts.items():
			print host, info

	host_info = get_hosts_status()

	if request.method == 'POST':
		action = request.POST.get('action','')
		if action == 'delete':
			host = request.POST.get('host','')
			del_host(host)
			return HttpResponseRedirect('/dashboard/')
		if action == 'add':
			name = request.POST.get('name','')
			ipaddr = request.POST.get('ipaddr','')
			login = request.POST.get('sshusr','')
			passw = request.POST.get('passw','')
			add_host(name, ipaddr, login, passw)
			return HttpResponseRedirect('/dashboard/')
	return render_to_response('dashboard.html', locals())
