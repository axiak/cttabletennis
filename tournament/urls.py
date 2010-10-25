from django.conf.urls.defaults import *

urlpatterns = patterns('tournament.views',
         (r'create_division/?', 'load_divisions'),
)
