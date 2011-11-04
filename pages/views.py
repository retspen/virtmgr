from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/usr/login/')
	else:
		return HttpResponseRedirect('/hosts/')

def about(request):
	return render_to_response('about.html')

def support(request):
	return render_to_response('support.html')

def help(request):
	return render_to_response('help.html')

def privacy(request):
	return render_to_response('privacy.html')

def faq(request):
	return render_to_response('faq.html')
