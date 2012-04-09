import registration
from django import forms
from virtmgr.model.models import *

class AddNewHost(forms.Form): 
	name = forms.CharField(required=False) 
	ipaddr = forms.CharField(required=False) 
	sshusr = forms.CharField(required=False)
	passw = forms.CharField(required=False)

	def clean_name(self):
		name = self.cleaned_data['name']
		hostname = Host.objects.filter(user=request.user, hostname=name)
		if hostname:
			raise forms.ValidationError("Hostname alredy exist!")
		return name

	def clean_ipaddr(self):
		ip = self.cleaned_data['ipaddr']
		ipaddr = Host.objects.filter(user=request.user, ipaddr=ip)
		if ipaddr:
			raise forms.ValidationError("IP adress alredy exist!")
		return ip


