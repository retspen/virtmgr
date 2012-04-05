from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect

def index(request):
	if request.user.is_authenticated():
		return HttpResponseRedirect('/newhosts/')
	else:
		return render_to_response('index.html')

def about(request):

	return render_to_response('about.html')

def support(request):
	return render_to_response('support.html')

def docs(request):
	return render_to_response('docs.html')

def settings(request):
	return render_to_response('settings.html')

def faq(request):
	return render_to_response('faq.html')