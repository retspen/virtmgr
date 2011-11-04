from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect

def index(request):
    return render_to_response('index.html', locals())