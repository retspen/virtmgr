from django.conf.urls.defaults import patterns, include, url
from virtmgr import settings
from registration.forms import RegistrationFormUniqueEmail
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Static pages
    url(r'^$', 'virtmgr.pages.views.index'),
    url(r'^about/', 'virtmgr.pages.views.about'),
    url(r'^support/', 'virtmgr.pages.views.support'),
    url(r'^settings/', 'virtmgr.pages.views.settings'),
    url(r'^faq/', 'virtmgr.pages.views.faq'),

    # Users
    url(r'^user/register/$', 'registration.views.register', {'form_class': RegistrationFormUniqueEmail, 'backend': 'registration.backends.default.DefaultBackend'}, name='registration_register'),
    url(r'^user/', include('registration.urls')),
    url(r'^user/profile/$', include('registration.urls')),
    
    # Newhost
    url(r'^newhosts/$', 'virtmgr.newhosts.views.index'),

    # Servers
    url(r'^hosts/', 'virtmgr.hosts.views.index'),

    # NewVM
    url(r'^newvm/(\w+)/$', 'virtmgr.newvm.views.index'),
    url(r'^newvm/', 'virtmgr.newvm.views.redir'),

    # Overview
    url(r'^overview/(\w+)/$', 'virtmgr.overview.views.index'),
    url(r'^overview/', 'virtmgr.overview.views.redir'),

    # Storage
    url(r'^storage/(\w+)/$', 'virtmgr.storage.views.index'),
    url(r'^storage/(\w+)/(\w+)/$', 'virtmgr.storage.views.pool'),
    url(r'^storage/', 'virtmgr.storage.views.redir'),

    # Network
    url(r'^network/(\w+)/$', 'virtmgr.network.views.index'),
    url(r'^network/(\w+)/(\w+)/$', 'virtmgr.network.views.pool'),
    url(r'^network/', 'virtmgr.network.views.redir'),

    # Interfaces
    #url(r'^interfaces/(\w+)/$', 'virtmgr.interfaces.views.index'),
    #url(r'^interfaces/(\w+)/(\w+)/$', 'virtmgr.interfaces.views.ifcfg'),
    #url(r'^interfaces/', 'virtmgr.interfaces.views.redir'),

    # VM
    url(r'^vm/(\w+)/(\w+)/$', 'virtmgr.vm.views.index'),
    url(r'^vm/(\w+)/$', 'virtmgr.vm.views.redir_two'),
    url(r'^vm/', 'virtmgr.vm.views.redir_one'),

    # VNC
    url(r'^vnc/(\w+)/(\w+)/$', 'virtmgr.vnc.views.index'),
    url(r'^vnc/(\w+)/$', 'virtmgr.vnc.views.redir_two'),
    url(r'^vnc/', 'virtmgr.vnc.views.redir_one'),
    
    # Media
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': False}),

    # Uncomment the next line to enable the admin:
    url(r'^vrtadm/', include(admin.site.urls)),
)
