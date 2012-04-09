# -*- coding: utf-8 -*-
import libvirt
import virtinst.util as util
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from virtmgr.model.models import *

def get_storages(conn):
	try:
		storages = []
		for name in conn.listStoragePools():
			storages.append(name)
		for name in conn.listDefinedStoragePools():
			storages.append(name)
		return storages
	except:
		print "Get storage failed"

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

 	usr_id = request.user.id
	usr_name = request.user
	kvm_host = Host.objects.get(user=usr_id,hostname=host)
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
	storages = get_storages(conn)

	if storages == None:
		return HttpResponseRedirect('/overview/' + host + '/')
	elif len(storages) == 0:
		return HttpResponseRedirect('/storage/' + host + '/new_stg_pool/')
	else:
		return HttpResponseRedirect('/storage/' + host + '/' + storages[0] + '/')

def pool(request, host, pool):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

 	usr_id = request.user.id
	usr_name = request.user
	kvm_host = Host.objects.get(user=usr_id,hostname=host)
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
		stg = conn.storagePoolLookupByName(pool)
		return stg

	def pool_start():
		stg.create(0)

	def pool_stop():
		stg.destroy()

	def pool_delete():
		stg.undefine()

	def pool_refresh():
		stg.refresh(0)

	def get_stg_info(get):
		try:
			if get == "info":
				return stg.info()
			elif get == "status":
				return stg.isActive()
			elif get == "start":
				return stg.autostart()
			elif get == "list":
				return stg.listVolumes()
		except:
			print "Not get pool info"

	def get_type():
		xml = stg.XMLDesc(0)
		return util.get_xml_path(xml, "/pool/@type")

	def get_target_path():
		xml = stg.XMLDesc(0)
		return util.get_xml_path(xml, "/pool/target/path")

	def delete_volume(img):
		vol = stg.storageVolLookupByName(img)
		vol.delete(0)

	def stg_set_autostart(pool):
		stg = conn.storagePoolLookupByName(pool)
		stg.setAutostart(1)

	def create_volume(img, size_max, size_aloc, format):
		xml = """
			<volume>
				<name>%s.img</name>
				<capacity>%s</capacity>
				<allocation>%s</allocation>
				<target>
					<format type='%s'/>
				</target>
			</volume>""" % (img, size_max, size_aloc, format)
		stg.createXML(xml,0)

	def create_stg_pool(type_pool, name_pool, path_pool):
		xml = """
			<pool type='%s'>
				<name>%s</name>
					<target>
						<path>%s</path>
					</target>
			</pool>""" % (type_pool, name_pool, path_pool)
		conn.storagePoolDefineXML(xml,0)

	def get_vl_info(listvol):
		volinfo = {}
		if stg.isActive() != 0:
			for name in listvol:
				vol = stg.storageVolLookupByName(name)
				xml = vol.XMLDesc(0)

				size = vol.info()[1]
				format = util.get_xml_path(xml, "/volume/target/format/@type")
 				volinfo[name] = size,format
		return volinfo
	
	conn = vm_conn(host_ip, creds)

	if conn == None:
		return HttpResponseRedirect('/overview/' + host + '/')

	pools = get_storages(conn)

	if pool == "new_stg_pool":
		if request.method == 'POST':
			name_pool = request.POST.get('name_pool','')
			path_pool = request.POST.get('path_pool','')
			type_pool = request.POST.get('type_pool','')
			errors = []
			if not name_pool:
				errors.append(u'Введите имя пула')
			if not path_pool:
				errors.append(u'Введите путь пула')
			if not errors:
				create_stg_pool(type_pool, name_pool, path_pool)
				stg = get_conn_pool(name_pool)
				pool_start()
				stg_set_autostart(name_pool)
				return HttpResponseRedirect('/storage/' + host + '/' + name_pool + '/')
		return render_to_response('storage_new.html', locals())

	stg = get_conn_pool(pool)
	status = get_stg_info('status')
	if status == 1:
		pool_refresh()
	info = get_stg_info('info')
	stype = get_type()
	spath = get_target_path()
	start = get_stg_info('start')
	listvol = get_stg_info('list')
	volinfo = get_vl_info(listvol)

	if request.method == 'POST':
		if request.POST.get('stop_pool',''):
			pool_stop()
		if request.POST.get('start_pool',''):
			pool_start()
		if request.POST.get('del_pool',''):
			pool_delete()
			return HttpResponseRedirect('/storage/' + host + '/')

		if request.POST.get('vol_del',''):
			img = request.POST['img']
			delete_volume(img)
			return HttpResponseRedirect('/storage/' + host + '/' + pool + '/')
		if request.POST.get('vol_add',''):
			img = request.POST['img']
			size_max = request.POST['size_max']
			size_aloc = request.POST['size_aloc']
			format = request.POST['format']
			errors = []
			if not img:
				errors.append(u'Введите имя образа')
			if not size_max:
				errors.append(u'Введите размер образа')
			if not errors:
				size_max = int(size_max) * 1048576
				if size_aloc != "0":
					size_aloc = int(size_aloc) * 1048576
				else:
					size_aloc = "0"	
				create_volume(img, size_max, size_aloc, format)
				return HttpResponseRedirect('/storage/' + host + '/' + pool + '/')
				
	return render_to_response('storage.html', locals())

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	else:
		return HttpResponseRedirect('/dashboard/')