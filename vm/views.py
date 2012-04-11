# -*- coding: utf-8 -*-
import re
import libvirt
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

def index(request, host, vname):

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
         return mem
      except:
         return "error"

   def get_vm_cpu():
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
         hdd = util.get_xml_path(xml, "/domain/devices/disk[1]/source/@file")
         #hdd = re.sub('\/.*\/','', hdd)
         return hdd
      except:
         return "error"

   def get_vm_cdrom():
      try:
         xml = dom.XMLDesc(0)
         cdrom = util.get_xml_path(xml, "/domain/devices/disk[2]/source/@file")
         #cdrom = re.sub('\/.*\/','', cdrom)
         return cdrom
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
         cdrom = get_vm_cdrom()
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
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      except:
         return "error"

   def get_vm_state():
      try:
         return dom.info()[0]
      except:
         return "error"

   conn = vm_conn(host_ip, creds)
   errors = []

   if conn == None:
      return HttpResponseRedirect('/overview/' + host + '/')

   all_vm = get_vms(conn)
   dom = get_dom(conn, vname)
   active = get_vm_active()
   state = get_vm_state()
   uuid = get_vm_uuid()
   memory = get_vm_mem()
   memory = int(memory) * 1024
   cpu =  get_vm_cpu()
   autostart = get_vm_autostart()
   vnc_port = get_vm_vnc()
   hdd = get_vm_hdd()
   boot_menu = get_vm_boot_menu()
   cdrom = get_vm_cdrom()
   storages = get_storages(conn)
   isos = find_all_iso()

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
            return HttpResponseRedirect('/overview/%s/' % host)
         except:
            return "error"
      if not errors:
         return HttpResponseRedirect('/vm/' + host + '/' + vname +'/')
      else:
         return render_to_response('vm.html', locals())
   
   return render_to_response('vm.html', locals())

def redir_two(request, host):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/')
   else:
      return HttpResponseRedirect('/dashboard')

def redir_one(request):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/')
   else:
      return HttpResponseRedirect('/dashboard/')