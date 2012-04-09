from django import forms
from virtmgr.model.models import *

class ContactForm(forms.Form): 
	name = forms.CharField(required=False) 
	ipaddr = forms.CharField(required=False) 
	sshusr = forms.CharField(required=False)
	passw = forms.CharField(required=False)

	def clean_name(self):
		name = self.cleaned_data['name']
		ip = self.cleaned_data['ipaddr']
		hostname = Host.objects.filter(user=request.user, hostname=name)
		ipaddr = Host.objects.filter(user=request.user, ipaddr=ip)
		if hostname:
			raise forms.ValidationError("Hostname alredy exist!")
		if ipaddr:
			raise forms.ValidationError("IP adress alredy exist!")
		return name, ip

