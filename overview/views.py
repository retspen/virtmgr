import libvirt
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from virtmgr.model.models import *

def index(request, host):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	usr_id = request.user.id
	kvm_host = Host.objects.get(user=usr_id,hostname=host)
	usr_name = request.user

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
		   	conn = libvirt.openAuth(uri, auth, 0)
		   	return conn
		except:
			print "Not connected"

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
			print "Get vm failed"

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
			print 'Get info failed'
		
	conn = vm_conn()
	all_vm = get_all_vm()
	info = get_info()
		
	return render_to_response('overview.html', locals())

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	else:
		return HttpResponseRedirect('/hosts')