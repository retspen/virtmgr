import libvirt
import re
import virtinst.util as util
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from virtmgr.model.models import *

def index(request, host):

   	if not request.user.is_authenticated():
	   	return HttpResponseRedirect('/login')

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
		vname = {}
		for id in conn.listDomainsID():
			id = int(id)
			dom = conn.lookupByID(id)
			vname[dom.name()] = dom.info()[0]
		for id in conn.listDefinedDomains():
			dom = conn.lookupByName(id)
			vname[dom.name()] = dom.info()[0]
		return vname
	
	def get_all_stg():
		storages = []
		for name in conn.listStoragePools():
			storages.append(name)
		for name in conn.listDefinedStoragePools():
			storages.append(name)
		return storages

	def get_all_net():
		networks = []
		for name in conn.listNetworks():
			networks.append(name)
		for name in conn.listDefinedNetworks():
			networks.append(name)
		# Not support all distro but Fedora!!!
		#for ifcfg in conn.listInterfaces():
		#	if ifcfg != 'lo' and not re.findall("eth", ifcfg):
		#		networks.append(ifcfg)
		#for ifcfg in conn.listDefinedInterfaces():
		#	if ifcfg != 'lo' and not re.findall("eth", ifcfg):
		#		networks.append(ifcfg)
		return networks
	
	def get_arch():
		arch = conn.getInfo()[0]
		return arch

	def find_all_iso():
		iso = []
		for storage in storages:
			stg = conn.storagePoolLookupByName(storage)
			stg.refresh(0)
			for img in stg.listVolumes():
				if re.findall(".iso", img) or re.findall(".ISO", img):
					iso.append(img)
		return iso

	def find_all_img():
		disk = []
		for storage in storages:
			stg = conn.storagePoolLookupByName(storage)
			stg.refresh(0)
			for img in stg.listVolumes():
				if re.findall(".img", img) or re.findall(".IMG", img):
					disk.append(img)
		return disk
	
	def get_img_path(vol):
		for storage in storages:
			stg = conn.storagePoolLookupByName(storage)
			for img in stg.listVolumes():
				if vol == img:
					vl = stg.storageVolLookupByName(vol)
					return vl.path() 

	def get_img_format(vol):
		for storage in storages:
			stg = conn.storagePoolLookupByName(storage)
			for img in stg.listVolumes():
				if vol == img:
					vl = stg.storageVolLookupByName(vol)
					xml = vl.XMLDesc(0)
					format = util.get_xml_path(xml, "/volume/target/format/@type")
					return format 

	def get_cpus():
		try:
			info = conn.getInfo()[2]
			return info
		except:
			print 'Get info failed'

	def get_emulator():
		try:
			emulator = []
			xml = conn.getCapabilities()
			arch = conn.getInfo()[0]
			if arch == 'x86_64':
				emulator.append(util.get_xml_path(xml,"/capabilities/guest[1]/arch/@name"))
				emulator.append(util.get_xml_path(xml,"/capabilities/guest[2]/arch/@name"))
			else:
				emulator = util.get_xml_path(xml,"/capabilities/guest[1]/arch/@name")
			return emulator
		except:
			print 'Get emulator failed'

	def get_machine():
		try:
			xml = conn.getCapabilities()
			machine = util.get_xml_path(xml,"/capabilities/guest/arch/machine/@canonical")
			return machine
		except:
			print 'Get info failed'

	
	def add_vm(name, mem, cpus, arch, machine, emul, machine, img_frmt, img, iso, bridge):
		memaloc = mem
		xml = """<domain type='kvm'>
				  <name>%s</name>
				  <memory>%s</memory>
				  <currentMemory>%s</currentMemory>
				  <vcpu>%s</vcpu>
				  <os>
				    <type arch='%s' machine='%s'>hvm</type>
				    <boot dev='hd'/>
				    <boot dev='cdrom'/>
				    <bootmenu enable='yes'/>
				  </os>
				  <features>
				    <acpi/>
				    <apic/>
				    <pae/>
				  </features>
				  <clock offset='utc'/>
				  <on_poweroff>destroy</on_poweroff>
				  <on_reboot>restart</on_reboot>
				  <on_crash>restart</on_crash>
				  <devices>""" % (name, mem, memaloc, cpus, arch, machine)
			
		if arch = 'x86_64':
			xml += """<emulator>%s</emulator>""" % (emul[1])
		else:
			xml += """<emulator>%s</emulator>""" % (emul[0])

			xml += """<disk type='file' device='disk'>
				      <driver name='qemu' type='%s'/>
				      <source file='%s'/>
				      <target dev='hda' bus='ide'/>
				      <address type='drive' controller='0' bus='0' unit='0'/>
				    </disk>
				    <disk type='file' device='cdrom'>
				      <driver name='qemu' type='raw'/>
				      <source file='%s'/>
				      <target dev='hdc' bus='ide'/>
				      <readonly/>
				      <address type='drive' controller='0' bus='1' unit='0'/>
				    </disk>
				    <controller type='ide' index='0'>
				      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>
				    </controller>
				    """ % (img_frmt, img, iso)

		if re.findall("br", bridge):
			xml += """<interface type='bridge'>
					<source bridge='%s'/>""" % (bridge)
		else:
			xml += """<interface type='network'>
					<source network='%s'/>""" % (bridge)
			
			xml += """<address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
				    </interface>
				    <input type='tablet' bus='usb'/>
				    <input type='mouse' bus='ps2'/>
				    <graphics type='vnc' port='-1' autoport='yes'/>
				    <video>
				      <model type='cirrus' vram='9216' heads='1'/>
				      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
				    </video>
				    <memballoon model='virtio'>
				      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
				    </memballoon>
				  </devices>
				</domain>"""
		conn.defineXML(xml)

	conn = vm_conn()

	if conn == None:
		return HttpResponseRedirect('/overview/' + host + '/')

	cores = get_cpus()
	all_vm = get_all_vm()
	storages = get_all_stg()
	all_iso = find_all_iso()
	all_img = find_all_img()
	bridge = get_all_net()
	arch = get_arch()
	emul = get_emulator()
	machine = get_machine()

	# Core CPUS
	cpus = []
	for cpu in range(1,cores+1):
		cpus.append(cpu)

	if request.method == 'POST':
		name = request.POST.get('name','')
		mem = request.POST.get('memory','')
		cpus = request.POST.get('cpus','')
		iso = request.POST.get('iso','')		
		img = request.POST.get('img','')
		bridge = request.POST.get('bridge','')
		arch = request.POST.get('arch','') 
		mem = int(mem) * 1024
		hdd = get_img_path(img)
		cdrom = get_img_path( iso)
		hdd_frmt = get_img_format( img)
		add_vm(name, mem, cpus, arch, machine, emul, hdd_frmt, hdd, cdrom, bridge)
		return HttpResponseRedirect('/vm/' + host + '/' + name + '/')

	return render_to_response('newvm.html', locals())

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	else:
		return HttpResponseRedirect('/hosts/')