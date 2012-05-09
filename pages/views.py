# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import translation

def index(request):
	#request.session['language'] = 'en'
	#translation.activate('en')
	request.session['django_language'] = 'en'
	if request.user.is_authenticated():
		return HttpResponseRedirect('/dashboard/')
	else:
		return render_to_response('index.html', locals())

def features(request):
	return render_to_response('features.html', locals())

def support(request):
	return render_to_response('support.html', locals())

def screenshot(request):
	return render_to_response('screenshot.html', locals())

def docs(request):
	return render_to_response('docs.html', locals())

def settings(request):
	return render_to_response('settings.html', locals())

def faq(request):
	return render_to_response('faq.html', locals())