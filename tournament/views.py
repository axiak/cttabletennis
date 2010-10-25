import itertools

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.simple import direct_to_template

from tournament.models import *

@staff_member_required
def load_divisions(request):
    if request.method == 'GET':
        return direct_to_template(request, 'tournament/create_divisions.html')
    division_data = request.POST['data'].replace('\r\n', '\n')

    teams = dict((get_name(team), team) for team in Team.objects.all())
    t = Tournament.objects.get()

    Division.objects.all().delete()
    Match.objects.all().delete()

    for division in division_data.split('\n\n'):
        division = division.strip()
        lines = division.splitlines()
        name = lines[0]
        teams_list = [teams[line] for line in lines[1:]]
        d = Division.objects.create(name=name, tournament=t)
        d.teams = teams_list
        d.save()
        for team1, team2 in itertools.combinations(teams_list, 2):
            match_type = 'double' if team1.player2 else 'single'
            m = Match.objects.create(team1=team1, team2=team2,
                                     best_of=3, match_type=match_type,
                                     parent_division=d)
    return HttpResponse("Divisions Created!")

def get_name(team):
        players = [team.player1]
        if team.player2:
            players.append(team.player2)
        return ' and '.join(sorted([player.user.username for player in players]))
