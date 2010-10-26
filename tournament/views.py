import itertools
import datetime

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.simple import direct_to_template
from django.core.cache import cache

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
        for team1, team2 in combinations(teams_list, 2):
            match_type = 'double' if team1.player2 else 'single'
            m = Match.objects.create(team1=team1, team2=team2,
                                     best_of=3, match_type=match_type,
                                     parent_division=d)
    return HttpResponse("Divisions Created!")

def view_divisions(request):
    t = Tournament.objects.get()
    singles_key = '%s__singles_div' % t.pk
    doubles_key = '%s__doubles_div' % t.pk
    timeout = 86400
    singles_divisions = cache.get(singles_key)
    doubles_divisions= cache.get(doubles_key)
    if doubles_divisions is None or singles_divisions is None:
        d = list(Division.objects.filter(tournament = t))
        d.sort(key = lambda x: x.pk)
        singles_divisions = []
        doubles_divisions = []
        for division in d:
            for team in division.teams:
                team.player1
                team.player2
            if division.is_double():
                doubles_divisions.append(division)
            else:
                singles_divisions.append(division)
        cache.set(singles_key, singles_divisions, timeout)
        cache.set(doubles_key, doubles_divisions, timeout)
    return direct_to_template(request, 'tournament/divisions.html',
                              {'singles': singles_divisions,
                               'doubles': doubles_divisions})

def view_team(request, team_pk):
    team = Team.objects.get(pk = team_pk)
    wins, losses, matches = team.stats()
    def dvl(x, d):
        if x is None:
            return d
        else:
            return x
    old_datetime = datetime.datetime(1900, 1, 1, 0, 0)
    old_date = datetime.date(1900, 1, 1)
    matches.sort(key=lambda x: (dvl(x.played, old_date), dvl(x.score_recorded, old_datetime)), reverse=True)
    future, historical = [], []
    for match in matches:
        other_team = match.team1
        if other_team == team:
            other_team = match.team2
        val = {'match': match, 'other_team': other_team}
        if match.team1_scores:
            val['win'] = match.winner() == team
            val['scores'] = zip(match.team1_scores, match.team2_scores)
            historical.append(val)
        else:
            future.append(val)
    context = {'team': team,
               'wins': wins,
               'losses': losses,
               'future': future,
               'historical': historical}

    if team.player2:
        return direct_to_template(request, 'tournament/team_profile.html',
                                  context)
    else:
        context['player'] = team.player1
        return direct_to_template(request, 'tournament/player_profile.html',
                                  context)



def combinations(iterable, r):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = range(r)
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)

def get_name(team):
        players = [team.player1]
        if team.player2:
            players.append(team.player2)
        return ' and '.join(sorted([player.user.username for player in players]))
