# -*- coding: utf-8 -*-
import libvirt, re
import virtinst.util as util
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from virtmgr.model.models import *

def get_storages(conn):
	try:
		storages = {}
		for name in conn.listStoragePools():
			stg = conn.storagePoolLookupByName(name)
			status = stg.isActive()
			storages[name] = status
		for name in conn.listDefinedStoragePools():
			stg = conn.storagePoolLookupByName(name)
			status = stg.isActive()
			storages[name] = status
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
		return "error"

def index(request, host_id):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	kvm_host = Host.objects.get(user=request.user.id, id=host_id)
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
		return HttpResponseRedirect('/overview/%s/' % (host_id))
	elif len(storages) == 0:
		return HttpResponseRedirect('/storage/%s/new_stg_pool/' % (host_id))
	else:
		return HttpResponseRedirect('/storage/%s/%s/' % (host_id, storages.keys()[0]))

def pool(request, host_id, pool):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	kvm_host = Host.objects.get(user=request.user.id, id=host_id)
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
		try:
			stg = conn.storagePoolLookupByName(pool)
			return stg
		except:
			return "error"

	def pool_start():
		try:
			stg.create(0)
		except:
			return "error"

	def pool_stop():
		try:
			stg.destroy()
		except:
			return "error"

	def pool_delete():
		try:
			stg.undefine()
		except:
			return "error"
			
	def pool_refresh():
		try:
			stg.refresh(0)
		except:
			return "error"

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
			return "error"

	def get_type():
		try:
			xml = stg.XMLDesc(0)
			return util.get_xml_path(xml, "/pool/@type")
		except:
			return "error"

	def get_target_path():
		try:
			xml = stg.XMLDesc(0)
			return util.get_xml_path(xml, "/pool/target/path")
		except:
			return "error"

	def delete_volume(img):
		try:
			vol = stg.storageVolLookupByName(img)
			vol.delete(0)
		except:
			return "error"

	def stg_set_autostart(pool):
		try:
			stg = conn.storagePoolLookupByName(pool)
			stg.setAutostart(1)
		except:
			return "error"

	def create_volume(img, size_max, format):
		try:
			size_max = int(size_max) * 1073741824
			xml = """
				<volume>
					<name>%s.img</name>
					<capacity>%s</capacity>
					<allocation>0</allocation>
					<target>
						<format type='%s'/>
					</target>
				</volume>""" % (img, size_max, format)
			stg.createXML(xml,0)
		except:
			return "error"

	def create_stg_pool(type_pool, name_pool, path_pool):
		try:
			xml = """
				<pool type='%s'>
					<name>%s</name>
						<target>
							<path>%s</path>
						</target>
				</pool>""" % (type_pool, name_pool, path_pool)
			conn.storagePoolDefineXML(xml,0)
		except:
			return "error"

	def get_vl_info(listvol):
		try:
			volinfo = {}
			if stg.isActive() != 0:
				for name in listvol:
					vol = stg.storageVolLookupByName(name)
					xml = vol.XMLDesc(0)
					size = vol.info()[1]
					format = util.get_xml_path(xml, "/volume/target/format/@type")
	 				volinfo[name] = size,format
			return volinfo
		except:
			return "error"
	
	conn = vm_conn(host_ip, creds)
	errors = []

	if conn == None:
		return HttpResponseRedirect('/overview/%s/' % (host_id))

	pools = get_storages(conn)

	if pool == "new_stg_pool":
		if request.method == 'POST':
			name_pool = request.POST.get('name_pool','')
			path_pool = request.POST.get('path_pool','')
			type_pool = request.POST.get('type_pool','')
			simbol = re.search('[^a-zA-Z0-9\_]+', name_pool)
			if len(name_pool) > 20:
				errors.append(u'Название пула не должно быть больше чем 20 символов')
			if simbol:
				errors.append(u'Название пула не должно содержать символы и русские буквы')
			if not name_pool:
				errors.append(u'Введите имя пула')
			if not path_pool:
				errors.append(u'Введите путь пула')
			if not errors:
				if create_stg_pool(type_pool, name_pool, path_pool) is "error":
					errors.append(u'Возможно пул с такими данными существует')
				else:
					stg = get_conn_pool(name_pool)
					stg_set_autostart(name_pool)
					if pool_start() is "error":
						errors.append(u'Пул создан, но при запуске пула возникла ошибка, возможно указан не существующий путь')
					else:
						return HttpResponseRedirect('/storage/%s/%s/' % (host_id, name_pool))
				if errors:
					return render_to_response('storage_new.html', locals())
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
			return HttpResponseRedirect('/storage/%s/%s/' % (host_id, pool))
		if request.POST.get('start_pool',''):
			pool_start()
			return HttpResponseRedirect('/storage/%s/%s/' % (host_id, pool))
		if request.POST.get('del_pool',''):
			pool_delete()
			return HttpResponseRedirect('/storage/%s/' % (host_id))
		if request.POST.get('vol_del',''):
			img = request.POST['img']
			delete_volume(img)
			return HttpResponseRedirect('/storage/%s/%s/' % (host_id, pool))
		if request.POST.get('vol_add',''):
			img = request.POST['img']
			size_max = request.POST['size_max']
			format = request.POST['format']
			errors = []
			if not img:
				errors.append(u'Введите имя образа')
			if not size_max:
				errors.append(u'Введите размер образа')
			if not errors:
				create_volume(img, size_max, format)
				return HttpResponseRedirect('/storage/%s/%s/' % (host_id, pool))

	conn.close()
				
	return render_to_response('storage.html', locals())

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	else:
		return HttpResponseRedirect('/dashboard/')