players = '''Michael Axiak and Scott Leclaire
Mark Pellegrino and Mohit Dilawari
Glenn Evershed and John Carter
David Daugherty and Jonathan Foley
Jeena Dongol and Bill Bellissimo
Brad Pielech and Eileen Murray
Elena Salgannik and James Krawczynski
Lawrence Zhao and Trilok Mummareddy
Satyajit Heeralal and Wojtek Golly
Divyang Patel and Chris Orth
Andrew Monat and Eric Abbott
Lav Rajbanshi and Adam Buggia
Vladimir Shclover and Brandon Zyxnfryx
Feng Xia and Jimmy Lam'''

from django.http import *
from tournament.models import *
from django.contrib.auth.models import *

import datetime

superusers = ('maxiak', 'sheeralal', 'bpielech')

def load_players(request):
    t = Tournament.objects.create(start_date=datetime.date(2010, 11, 1),
                                  end_date = datetime.date(2010, 11, 19),
                                  name="CrunchTime! 2010 Fall Tournament")
    t.save()
    for row in players.splitlines():
        player1, player2 = map(get_player, row.split(' and '))
        team1 = Team.objects.create(player1=player1)
        team1.save()
        team2 = Team.objects.create(player1=player2)
        team2.save()
        team3 = Team.objects.create(player1=player1, player2=player2)
        team3.save()
    return HttpResponse("CREATED PLAYERS!")

def get_player(s):
    username = s.lower().split()[0][0] + s.lower().split()[1]
    u = User.objects.create(first_name=s.split()[0], last_name = s.split()[1],
                            username = username,
                            email = '%s@crunchtime.com' % username)
    u.set_password(username)
    if username in superusers:
        u.is_active = True
        u.is_superuser = True
        u.is_staff = True
    u.save()
    p = Player.objects.create(user = u)
    p.save()
    return p
    
