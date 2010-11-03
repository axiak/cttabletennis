from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    ('^$', 'django.views.generic.simple.direct_to_template',
     {'template': 'home.html'}),
    ('^teams/?$', 'django.views.generic.simple.direct_to_template',
     {'template': 'teams.html'}),
    ('^live/?$', 'tournament.views.live'),
    ('^rules/?$', 'django.views.generic.simple.direct_to_template',
     {'template': 'rules.html'}),
    ('^blocked/$', 'django.views.generic.simple.direct_to_template',
     {'template': 'blocked.html'}),

                       ('^load_players', 'load_people.load_players'),
     
    (r'^setup/', include(admin.site.urls)),
    (r'^tournament/', include('tournament.urls')),
    (r'^login/$', 'django.contrib.auth.views.login',
       {'template_name': 'registration/login.html'}),

)
