import libvirt, re
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from virtmgr.model.models import *

def index(request, host):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login/')

	kvm_host = Host.objects.get(user=request.user.id,hostname=host)

	def creds(credentials, user_data):
		for credential in credentials:
			if credential[0] == libvirt.VIR_CRED_AUTHNAME:
				credential[4] = kvm_host.login
				if len(credential[4]) == 0:
					credential[4] = credential[3]
			elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
				credential[4] = kvm_host.passwd
			else:
				return -1
		return 0

  	def vm_conn():
  		flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
	   	auth = [flags, creds, None]
		uri = 'qemu+tcp://' + kvm_host.ipaddr + '/system'
	   	try:
	   		import socket
	   		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	   		s.settimeout(1)
	   		s.connect((kvm_host.ipaddr, 16509))
	   		s.close()
		   	conn = libvirt.openAuth(uri, auth, 0)
		   	return conn
		except:
			return "error"

	def get_all_vm():
		try:
			vname = {}
			for id in conn.listDomainsID():
				id = int(id)
				dom = conn.lookupByID(id)
				vname[dom.name()] = dom.info()[0]
			for id in conn.listDefinedDomains():
				dom = conn.lookupByName(id)
				vname[dom.name()] = dom.info()[0]
			return vname
		except:
			vname['000x'] = '000x'
			return vname

	def get_info():
		info = []
		try:
			info.append(conn.getURI())
			info.append(conn.getInfo()[0])
			info.append(conn.getInfo()[1])
			info.append(conn.getInfo()[2])
			info.append(conn.getInfo()[3])
			return info
		except:
			return "error"

	def get_capatib():
		try:
			hostcap = conn.getCapabilities()
			iskvm = re.search('kvm', hostcap)
			if iskvm:
				return 1
			else:
				return 0
		except:
			return "error"
		
	conn = vm_conn()
	all_vm = get_all_vm()
	info = get_info()
	iskvm = get_capatib()
		
	return render_to_response('overview.html', locals())

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login/')
	else:
		return HttpResponseRedirect('/dashboard/')