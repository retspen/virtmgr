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
      print "Get all vm failed"

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

def get_dom(conn, vname):
   try:
      dom = conn.lookupByName(vname)
      return dom
   except:
      print "Not connected"

def index(request, host, vname):

   if not request.user.is_authenticated():
      return HttpResponseRedirect('/')

   usr_id = request.user.id
   kvm_host = Host.objects.get(user=usr_id,hostname=host)
   usr_name = request.user
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
         print "Get domain status failed"

   def get_vm_uuid():
      xml = dom.XMLDesc(0)
      uuid = util.get_xml_path(xml, "/domain/uuid")
      return uuid

   def get_vm_mem():
      xml = dom.XMLDesc(0)
      mem = util.get_xml_path(xml, "/domain/currentMemory")
      return mem

   def get_vm_cpu():
      xml = dom.XMLDesc(0)
      cpu = util.get_xml_path(xml, "/domain/vcpu")
      return cpu

   def get_vm_vnc():
      xml = dom.XMLDesc(0)
      vnc = util.get_xml_path(xml, "/domain/devices/graphics/@port")
      return vnc

   def get_vm_hdd():
      xml = dom.XMLDesc(0)
      hdd = util.get_xml_path(xml, "/domain/devices/disk[1]/source/@file")
      return hdd

   def get_vm_cdrom():
      xml = dom.XMLDesc(0)
      cdrom = util.get_xml_path(xml, "/domain/devices/disk[2]/source/@file")
      return cdrom

   def get_vm_boot_menu():
      xml = dom.XMLDesc(0)
      boot_menu = util.get_xml_path(xml, "/domain/os/bootmenu/@enable")
      return boot_menu
   
   def mnt_iso_on(vol):
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

   def mnt_iso_off(vol):
      for storage in storages:
         stg = conn.storagePoolLookupByName(storage)
         for img in stg.listVolumes():
            if vol == img:
               vl = stg.storageVolLookupByName(vol)

      xml = dom.XMLDesc(0)
      iso = "<driver name='qemu' type='raw'/>\n<source file='%s'/>" % vl.path()
      xmldom = xml.replace("<driver name='qemu' type='raw'/>", iso)
      conn.defineXML(xmldom)

   def umnt_iso_on():
      xml = """<disk type='file' device='cdrom'>
                  <driver name="qemu" type='raw'/>
                  <target dev='hdc' bus='ide'/>
                  <readonly/>
               </disk>"""
      dom.attachDevice(xml)
      xmldom = dom.XMLDesc(0)
      conn.defineXML(xmldom)

   def umnt_iso_off():
      xml = dom.XMLDesc(0)
      cdrom = get_vm_cdrom()
      xmldom = xml.replace("<source file='%s'/>\n" % cdrom,"")
      conn.defineXML(xmldom)

   def find_all_iso():
      iso = []
      for storage in storages:
         stg = conn.storagePoolLookupByName(storage)
         stg.refresh(0)
         for img in stg.listVolumes():
            if re.findall(".iso", img) or re.findall(".ISO", img):
               iso.append(img)
      return iso
   
   def get_vm_autostart():
      return dom.autostart()

   def page_refresh():
      return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )

   def get_vm_state():
      return dom.info()[0]

   conn = vm_conn(host_ip, creds)

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
      action = request.POST.get('action','')
      iso = request.POST.get('iso_img','')
      
      if action == 'suspend':
         dom.suspend()
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      elif action == 'resume':
         dom.resume()
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      elif action == 'start':
         dom.create()
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      elif action == 'shutdown':
         dom.shutdown()
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      elif action == 'destroy':
         dom.destroy()
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      elif action == 'save':
         dom.save(0)
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      elif action == 'reboot':
         dom.destroy()
         dom.create()
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      elif action == 'auto ON':
         dom.setAutostart(1)
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      elif action == 'auto OFF':
         dom.setAutostart(0)
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      elif action == 'disconnect':
         if state == 1:
            umnt_iso_on()
         else:
            umnt_iso_off()
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      elif action == 'connect':
         if state == 1:
            mnt_iso_on(iso)
         else:
            mnt_iso_off(iso)
         return HttpResponseRedirect('/vm/' + host + '/' + vname + '/' )
      elif action == 'undefine':
         dom.undefine()
         return HttpResponseRedirect('/overview/' + host + '/')

   return render_to_response('vm.html', locals())

def redir_two(request, host):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/')
   else:
      return HttpResponseRedirect('/hosts')

def redir_one(request):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/')
   else:
      return HttpResponseRedirect('/hosts')