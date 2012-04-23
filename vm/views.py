# -*- coding: utf-8 -*-
import re
import libvirt
import time
import virtinst.util as util
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from virtmgr.model.models import *

def get_vms(conn):
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
     return "error"

def get_storages(conn):
   try:
      storages = []
      for name in conn.listStoragePools():
         storages.append(name)
      for name in conn.listDefinedStoragePools():
         storages.append(name)
      return storages
   except:
      return "error"

def vm_conn(host_ip, creds):
   try:
      flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
      auth = [flags, creds, None]
      uri = 'qemu+tcp://' + host_ip + '/system'
      conn = libvirt.openAuth(uri, auth, 0)
      return conn
   except:
      return "error"

def get_dom(conn, vname):
   try:
      dom = conn.lookupByName(vname)
      return dom
   except:
      return "error"

def index(request, host_id, vname):

   if not request.user.is_authenticated():
      return HttpResponseRedirect('/')

   kvm_host = Host.objects.get(user=request.user.id, id=host_id)

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

   def get_vm_active():
      try:
         state = dom.isActive()
         return state
      except:
         return "error"

   def get_vm_uuid():
      try:
         xml = dom.XMLDesc(0)
         uuid = util.get_xml_path(xml, "/domain/uuid")
         return uuid
      except:
         return "error"

   def get_vm_mem():
      try:
         xml = dom.XMLDesc(0)
         mem = util.get_xml_path(xml, "/domain/currentMemory")
         mem = int(mem) * 1024
         return mem
      except:
         return "error"

   def get_vm_core():
      try:
         xml = dom.XMLDesc(0)
         cpu = util.get_xml_path(xml, "/domain/vcpu")
         return cpu
      except:
         return "error"

   def get_vm_vnc():
      try:
         xml = dom.XMLDesc(0)
         vnc = util.get_xml_path(xml, "/domain/devices/graphics/@port")
         return vnc
      except:
         return "error"

   def get_vm_hdd():
      try:
         xml = dom.XMLDesc(0)
         hdd_path = util.get_xml_path(xml, "/domain/devices/disk[1]/source/@file")
         image = re.sub('\/.*\/','', hdd_path)
         size = dom.blockInfo(hdd_path, 0)[0]
         return image, size
      except:
         return "error"

   def get_vm_cdrom():
      try:
         xml = dom.XMLDesc(0)
         cdr_path = util.get_xml_path(xml, "/domain/devices/disk[2]/source/@file")
         if cdr_path:
            image = re.sub('\/.*\/','', cdr_path)
            size = dom.blockInfo(cdr_path, 0)[0]
            return image, cdr_path, size
         else:
            return cdr_path
      except:
         return "error"

   def get_vm_boot_menu():
      try:
         xml = dom.XMLDesc(0)
         boot_menu = util.get_xml_path(xml, "/domain/os/bootmenu/@enable")
         return boot_menu
      except:
         return "error"
      
   def mnt_iso_on(vol):
      try:
         for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
            for img in stg.listVolumes():
               if vol == img:
                  vl = stg.storageVolLookupByName(vol)
         xml = """<disk type='file' device='cdrom'>
                     <driver name='qemu' type='raw'/>
                     <target dev='hdc' bus='ide'/>
                     <source file='%s'/>
                     <readonly/>
                  </disk>""" % vl.path()
         dom.attachDevice(xml)
         xmldom = dom.XMLDesc(0)
         conn.defineXML(xmldom)
      except:
         return "error"

   def mnt_iso_off(vol):
      try:
         for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
            for img in stg.listVolumes():
               if vol == img:
                  vl = stg.storageVolLookupByName(vol)
         xml = dom.XMLDesc(0)
         iso = "<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>\n      <source file='%s'/>" % vl.path()
         xmldom = xml.replace("<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>", iso)
         conn.defineXML(xmldom)
      except:
         return "error"

   def umnt_iso_on():
      try:
         xml = """<disk type='file' device='cdrom'>
                     <driver name="qemu" type='raw'/>
                     <target dev='hdc' bus='ide'/>
                     <readonly/>
                  </disk>"""
         dom.attachDevice(xml)
         xmldom = dom.XMLDesc(0)
         conn.defineXML(xmldom)
      except:
         return "error"

   def umnt_iso_off():
      try:
         xml = dom.XMLDesc(0)
         cdrom = get_vm_cdrom()[1]
         xmldom = xml.replace("<source file='%s'/>\n" % cdrom,"")
         conn.defineXML(xmldom)
      except:
         return "error"

   def find_all_iso():
      try:
         iso = []
         for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
            stg.refresh(0)
            for img in stg.listVolumes():
               if re.findall(".iso", img) or re.findall(".ISO", img):
                  iso.append(img)
         return iso
      except:
         return "error"
   
   def get_vm_autostart():
      try:
         return dom.autostart()
      except:
         return "error"

   def page_refresh():
      try:
         return HttpResponseRedirect('/vm/' + host_id + '/' + vname + '/' )
      except:
         return "error"

   def get_vm_state():
      try:
         return dom.info()[0]
      except:
         return "error"

   def vm_cpu_usage():
      try:
         nbcore = conn.getInfo()[2]
         cpu_use_ago = dom.info()[4]
         time.sleep(1) 
         cpu_use_now = dom.info()[4]
         diff_usage = cpu_use_now - cpu_use_ago
         cpu_usage = 100 * diff_usage / (1 * nbcore * 10**9L)
         return cpu_usage
      except:
         return "error"

   def get_memusage():
      try:
         allmem = conn.getInfo()[1] * 1048576
         dom_mem = dom.info()[1] * 1024
         percent = (dom_mem * 100) / allmem
         return allmem, percent
      except:
         return "error"

   def get_all_core():
      try:
         allcore = conn.getInfo()[2]
         return allcore
      except:
         return "error"
   
   def vm_create_snapshot():
      try:
         xml = """<domainsnapshot>\n
                     <name>%d</name>\n
                     <state>shutoff</state>\n
                     <creationTime>%d</creationTime>\n""" % (time.time(), time.time())
         xml += dom.XMLDesc(0)
         xml += """<active>0</active>\n
                  </domainsnapshot>"""
         dom.snapshotCreateXML(xml,0)
      except:
         return "error"

   def get_snapshot_num():
      try:
         return dom.snapshotNum(0)
      except:
         return "error"

   conn = vm_conn(kvm_host.ipaddr, creds)
   errors = []

   if conn == None:
      return HttpResponseRedirect('/overview/' + host + '/')

   all_vm = get_vms(conn)
   dom = get_dom(conn, vname)
   active = get_vm_active()
   state = get_vm_state()
   uuid = get_vm_uuid()
   memory = get_vm_mem()
   core =  get_vm_core()
   autostart = get_vm_autostart()
   vnc_port = get_vm_vnc()
   hdd = get_vm_hdd()
   boot_menu = get_vm_boot_menu()
   cdrom = get_vm_cdrom()
   storages = get_storages(conn)
   isos = find_all_iso()
   all_core = get_all_core()
   cpu_usage = vm_cpu_usage()
   mem_usage = get_memusage()
   num_snapshot = get_snapshot_num()

   # Post form html
   if request.method == 'POST':
      if request.POST.get('suspend',''):
         try:
            dom.suspend()
         except:
            errors.append(u'Ошибка: возможно виртуальная машина уже приостаовлена')
      if request.POST.get('resume',''):
         try:
            dom.resume()
         except:
            errors.append(u'Ошибка: возможно виртуальная машина уже возобновлена')
      if request.POST.get('start',''):
         try:
            dom.create()
         except:
            errors.append(u'Ошибка: возможно виртуальная машина уже запущена')
      if request.POST.get('shutdown',''):
         try:
            dom.shutdown()
         except:
            errors.append(u'Ошибка: возможно виртуальная машина уже выключена')
      if request.POST.get('destroy',''):
         try:
            dom.destroy()
         except:
            errors.append(u'Ошибка: возможно виртуальная машина уже выключена')
      if request.POST.get('save',''):
         try:
            dom.save(0)
         except:
            errors.append(u'Ошибка: возможно виртуальная машина уже сохранена')
      if request.POST.get('reboot',''):
         try:
            dom.destroy()
            dom.create()
         except:
            errors.append(u'Ошибка: возникли проблемы при перезагрузке')
      if request.POST.get('snapshot',''):
         try:
            vm_create_snapshot()
         except:
            errors.append(u'Ошибка: при создании снапшота')
      if request.POST.get('auto_on',''):
         try:
            dom.setAutostart(1)
         except:
            return "error"
      if request.POST.get('auto_off',''):
         try:
            dom.setAutostart(0)
         except:
            return "error"
      if request.POST.get('disconnect',''):
         iso = request.POST.get('iso_img','')
         if state == 1:
            umnt_iso_on()
         else:
            umnt_iso_off()
      if request.POST.get('connect',''):
         iso = request.POST.get('iso_img','')     
         if state == 1:
            mnt_iso_on(iso)
         else:
            mnt_iso_off(iso)
      if request.POST.get('undefine',''):
         try:
            dom.undefine()
            return HttpResponseRedirect('/overview/%s/' % (host_id))
         except:
            return "error"
      if not errors:
         return HttpResponseRedirect('/vm/%s/%s/' % (host_id, vname))
      else:
         return render_to_response('vm.html', locals())

   conn.close()
   
   return render_to_response('vm.html', locals())

def redir_two(request, host_id):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/user/login')
   else:
      return HttpResponseRedirect('/dashboard')

def redir_one(request):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/user/login')
   else:
      return HttpResponseRedirect('/dashboard/')