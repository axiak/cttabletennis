import itertools

from collections import defaultdict

from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic.simple import direct_to_template
from django.core.cache import cache

from cachehelper.helper import cachelib

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

@cachelib.register_cache("view_divisions", model=Tournament, skip_pos=1, recompute=False)
def view_divisions_t(request, t):
    singles_divisions, doubles_divisions = t.get_divisions()
    return direct_to_template(request, 'tournament/divisions.html',
                              {'singles': singles_divisions,
                               'doubles': doubles_divisions})

def view_divisions(request):
    return view_divisions_t(request, Tournament.objects.get())

def view_players(request):
    return view_players_t(request, Tournament.objects.get())

@cachelib.register_cache("view_players", model=Tournament, skip_pos=1, recompute=False)
def view_players_t(request, t):
    singles_divisions, doubles_divisions = t.get_divisions()
    players = set()
    players_teams = defaultdict(list)
    for division in itertools.chain(singles_divisions, doubles_divisions):
        for team in division.teams:
            players_teams[team.player1].append(team)
            players.add(team.player1)
            if team.player2:
                players_teams[team.player2].append(team)
                players.add(team.player2)
    players = list(players)
    players.sort(key=lambda p: (p.user.first_name, p.user.last_name))
    for player in players:
        player.set_teams(players_teams[player])
    
    return direct_to_template(request, 'tournament/players.html',
                              {'players': players})



@cachelib.register_cache("view_player", model=Player, skip_pos=1, cache_timeout=3600, recompute=False)
def view_player(request, player_pk):
    player = Player.objects.get(pk=player_pk)
    total_wins, total_losses = 0, 0
    for team in player.get_teams():
        wins, losses, matches = team.stats()
        total_wins += wins
        total_losses += losses
    return direct_to_template(request, 'tournament/player_actual_profile.html',
                              {'player': player, 'wins': total_wins, 'losses': total_losses})

@cachelib.register_cache("view_team", model=Team, skip_pos=1, cache_timeout=3600, recompute=False)
def view_team(request, team_pk):
    team = Team.objects.get(pk = team_pk)
    wins, losses, matches = team.stats()
    historical, future = team.matches()
 
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
