from django.conf.urls.defaults import patterns, include, url
from virtmgr import settings
from registration.forms import RegistrationFormUniqueEmail
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^i18n/', include('django.conf.urls.i18n')),
    
    # Users
    url(r'^user/register/$', 'registration.views.register', {'form_class': RegistrationFormUniqueEmail, 'backend': 'registration.backends.default.DefaultBackend'}, name='registration_register'),
    url(r'^user/', include('registration.urls')),
    url(r'^user/profile/$', include('registration.urls')),

    # Static pages
    url(r'^$', 'virtmgr.pages.views.index'),
    url(r'^features/', 'virtmgr.pages.views.features'),
    url(r'^support/', 'virtmgr.pages.views.support'),
    url(r'^screenshot/', 'virtmgr.pages.views.screenshot'),
    url(r'^docs/$', 'virtmgr.pages.views.docs'),
    
    # Host
    url(r'^dashboard/$', 'virtmgr.dashboard.views.index'),

    # NewVM
    url(r'^newvm/(\d+)/$', 'virtmgr.newvm.views.index'),
    url(r'^newvm/', 'virtmgr.newvm.views.redir'),

    # Overview
    url(r'^overview/(\d+)/$', 'virtmgr.overview.views.index'),
    url(r'^overview/', 'virtmgr.overview.views.redir'),

    # Storage
    url(r'^storage/(\d+)/$', 'virtmgr.storage.views.index'),
    url(r'^storage/(\d+)/(\w+)/$', 'virtmgr.storage.views.pool'),
    url(r'^storage/', 'virtmgr.storage.views.redir'),

    # Network
    url(r'^network/(\d+)/$', 'virtmgr.network.views.index'),
    url(r'^network/(\d+)/(\w+)/$', 'virtmgr.network.views.pool'),
    url(r'^network/', 'virtmgr.network.views.redir'),

    # Snapshot
    url(r'^snapshot/(\d+)/$', 'virtmgr.snapshot.views.index'),
    url(r'^snapshot/(\d+)/(\w+)/$', 'virtmgr.snapshot.views.snapshot'),
    url(r'^snapshot/', 'virtmgr.snapshot.views.redir'),
    
    # Logs
    url(r'^logs/(\d+)/$', 'virtmgr.logs.views.logs'),
    url(r'^logs/', 'virtmgr.logs.views.redir'),

    # Interfaces
    #url(r'^interfaces/(\w+)/$', 'virtmgr.interfaces.views.index'),
    #url(r'^interfaces/(\w+)/(\w+)/$', 'virtmgr.interfaces.views.ifcfg'),
    #url(r'^interfaces/', 'virtmgr.interfaces.views.redir'),

    # VM
    url(r'^vm/(\d+)/(\w+)/$', 'virtmgr.vm.views.index'),
    url(r'^vm/(\d+)/$', 'virtmgr.vm.views.redir_two'),
    url(r'^vm/', 'virtmgr.vm.views.redir_one'),

    # VNC
    url(r'^vnc/(\d+)/(\w+)/$', 'virtmgr.vnc.views.index'),
    url(r'^vnc/(\d+)/$', 'virtmgr.vnc.views.redir_two'),
    url(r'^vnc/', 'virtmgr.vnc.views.redir_one'),
    
    # Media
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': False}),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
