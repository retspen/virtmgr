# -*- coding: utf-8 -*-
import libvirt
import virtinst.util as util
from virtmgr.network.IPy import IP
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from virtmgr.model.models import *

def get_networks(conn):
	try:
		networks = {}
		for name in conn.listNetworks():
			net.networkLookupByName(name)
			status = net.isActive()
			networks[name] = status
		for name in conn.listDefinedNetworks():
			net.networkLookupByName(name)
			status = net.isActive()
			networks[name] = status
		return networks
	except:
		print "Get network failed"

def vm_conn(host_ip, creds):
   	try:
		flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
  		auth = [flags, creds, None]
		uri = 'qemu+tcp://' + host_ip + '/system'
	   	conn = libvirt.openAuth(uri, auth, 0)
	   	return conn
	except:
		print "Not connected"

def index(request, host):
	
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	
	kvm_host = Host.objects.get(user=request.user.id,hostname=host)
	host_ip = kvm_host.ipaddr

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

	conn = vm_conn(host_ip, creds)
	networks = get_networks(conn)

	if networks == None:
		return HttpResponseRedirect('/overview/' + host + '/')
	elif len(networks) == 0:
		return HttpResponseRedirect('/network/' + host + '/new_net_pool')
	else:
		return HttpResponseRedirect('/network/' + host + '/' + networks[0] + '/')

def pool(request, host, pool):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	kvm_host = Host.objects.get(user=request.user.id,hostname=host)
	host_ip = kvm_host.ipaddr

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

	def get_conn_pool(pool):
		net = conn.networkLookupByName(pool)
		return net

	def pool_start():
		net.create()

	def pool_stop():
		net.destroy()

	def pool_delete():
		net.undefine()

	def net_set_autostart(pool):
		net = conn.networkLookupByName(pool)
		net.setAutostart(1)

	def get_net_info(get):
		try:
			if get == "bridge":
				return net.bridgeName()
			elif get == "status":
				return net.isActive()
			elif get == "start":
				return net.autostart()
		except:
			print "Get network info failed"	

	def get_ipv4_net():
		net = conn.networkLookupByName(pool)
		xml = net.XMLDesc(0)
		addrStr = util.get_xml_path(xml, "/network/ip/@address")
		netmaskStr = util.get_xml_path(xml, "/network/ip/@netmask")

		netmask = IP(netmaskStr)
		gateway = IP(addrStr)

		network = IP(gateway.int() & netmask.int())
		return IP(str(network) + "/" + netmaskStr)

	def get_ipv4_dhcp_range():
		net = conn.networkLookupByName(pool)
		xml = net.XMLDesc(0)
		dhcpstart = util.get_xml_path(xml, "/network/ip/dhcp/range[1]/@start")
		dhcpend = util.get_xml_path(xml, "/network/ip/dhcp/range[1]/@end")
		if not dhcpstart or not dhcpend:
			return None
		
		return [IP(dhcpstart), IP(dhcpend)]

	def get_ipv4_forward():
		xml = net.XMLDesc(0)
		fw = util.get_xml_path(xml, "/network/forward/@mode")
		forwardDev = util.get_xml_path(xml, "/network/forward/@dev")
		return [fw, forwardDev]

	def create_net_pool(name_pool, forward, ipaddr, netmask, dhcp, start_dhcp, end_dhcp):
		xml = """
			<network>
				<name>%s</name>""" % (name_pool)

		if forward == "nat" or "route":
			xml += """<forward mode='%s'/>""" % (forward)

		xml += """<bridge stp='on' delay='0' />
					<ip address='%s' netmask='%s'>""" % (gw_ipaddr, netmask)

		if dhcp == "yes":
			xml += """<dhcp>
						<range start='%s' end='%s' />
					</dhcp>""" % (start_dhcp, end_dhcp)
				
		xml += """</ip>
			</network>"""
		conn.networkDefineXML(xml)

	conn = vm_conn(host_ip, creds)

	if conn == None:
		return HttpResponseRedirect('/overview/' + host + '/')

	pools = get_networks(conn)

	if pool == "new_net_pool":
		if request.method == 'POST':
			name_pool = request.POST.get('name_pool','')
			net_addr = request.POST.get('net_addr','')
			forward = request.POST.get('forward','')
			dhcp = request.POST.get('dhcp','')
			errors = []
			if not name_pool:
				errors.append(u'Введите имя пула')
			if not net_addr:
				errors.append(u'Введите IP подсеть')
			if not errors:
				netmask = IP(net_addr).strNetmask()
				ipaddr = IP(net_addr)
				gw_ipaddr = ipaddr[1].strNormal()
				start_dhcp = ipaddr[2].strNormal()
				end_dhcp = ipaddr[254].strNormal()
				create_net_pool(name_pool, forward, gw_ipaddr, netmask, dhcp, start_dhcp, end_dhcp)
				net_set_autostart(name_pool)
				net = get_conn_pool(name_pool)
				pool_start()
				return HttpResponseRedirect('/network/' + host + '/' + name_pool + '/')
		return render_to_response('network_new.html', locals())

	net = get_conn_pool(pool)
	bridge = get_net_info('bridge')
	status = get_net_info('status')
	start = get_net_info('start')

	network = get_ipv4_net()
	dhcprange = get_ipv4_dhcp_range()
	netmode = get_ipv4_forward()

	if request.method == 'POST':
		if request.POST.get('stop_pool',''):
			pool_stop()
		if request.POST.get('start_pool',''):
			pool_start()
		if request.POST.get('del_pool',''):
			pool_delete()
			return HttpResponseRedirect('/network/' + host + '/')
		return HttpResponseRedirect('/network/' + host + '/' + pool + '/')

	return render_to_response('network.html', locals())

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	else:
		return HttpResponseRedirect('/dashboard')
