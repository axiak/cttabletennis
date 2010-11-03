from django.conf.urls.defaults import *

urlpatterns = patterns('tournament.views',
         (r'^divisions/?$', 'view_divisions'),
         (r'^players/?$', 'view_players'),
         url(r"^player/(\d+)/", 'view_player', name='view-player'),
         (r'^create_division/?$', 'load_divisions'),
         url(r'^teams/(\d+)/', 'view_team', name="view-team"),
         (r'^send_emails/?$', 'send_emails'),
)
