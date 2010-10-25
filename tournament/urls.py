from django.conf.urls.defaults import *

urlpatterns = patterns('tournament.views',
         (r'divisions/?$', 'view_divisions'),
         (r'create_division/?$', 'load_divisions'),
         url(r'teams/(\d+)/', 'view_team', name="view-team"),
)
