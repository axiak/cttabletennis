from django.core.management.base import BaseCommand, CommandError
from tournament.models import *
from django.contrib.auth import *

import random
import itertools

def chunk(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

DOUBLE_NAMES = '''Coffee Bean
Bubba Gump
Caribou'''.split('\n')

SINGLE_NAMES = '''Bone Daddy's
Joe's Crab Shack
Flying Star
Princess
CheeseCake
FuddRuckers
Wagamama'''.split('\n')

class Command(BaseCommand):
    args = ''
    help = 'Create divisions'

    def handle(self, *args, **options):
        teams = list(Team.objects.all())
        def team_type(team):
            return 0 if team.player2 is None else 1

        teams.sort(key=team_type)
        team_types = []
        for key, group in itertools.groupby(teams, team_type):
            team_types.append(list(group))
        singles, doubles = team_types

        self.generate_single_divisions(singles)
        self.generate_double_divisions(doubles)

    def generate_single_divisions(self, singles):
        def get_seed(team):
            return 0 if team.player1.seed is None else 1
        singles.sort(key=get_seed)
        single_seeds = [(), ()]
        for key, group in itertools.groupby(singles, get_seed):
            single_seeds[key] = list(group)
        rest, seeds = single_seeds
        r = random.SystemRandom()
        r.shuffle(seeds)
        for i in range(20):
            r.shuffle(rest)
        num_per_seed = len(rest) / len(seeds)
        for seed, division_name in zip(seeds, SINGLE_NAMES):
            print division_name
            print self.get_name(seed)
            current, rest = rest[:num_per_seed], rest[num_per_seed:]
            print "\n".join(self.get_name(t) for t in current)
            print
            
        

    def generate_double_divisions(self, doubles):
        r = random.SystemRandom()
        for i in range(20):
            r.shuffle(doubles)
        seed_lengths = [5, 5, 4]
        for length, name in zip(seed_lengths, DOUBLE_NAMES):
            print name
            current, doubles = doubles[:length], doubles[length:]
            print '\n'.join(self.get_name(t) for t in current)
            print
        

    def get_name(self, team):
        players = [team.player1]
        if team.player2:
            players.append(team.player2)
        return ' and '.join(sorted([player.user.username for player in players]))

        
