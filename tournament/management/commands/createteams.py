from django.core.management.base import BaseCommand, CommandError
from tournament.models import *
from django.contrib.auth import *

import random

def chunk(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

class Command(BaseCommand):
    args = ''
    help = 'Create doubles teams'

    def handle(self, *args, **options):
        p = list(Player.objects.all())
        r = random.SystemRandom()
        r.shuffle(p)
        while not self.valid_ordering(p):
            r.shuffle(p)
        for player1, player2 in chunk(p, 2):
            print "%s and %s" % (player1, player2)
            t = Team.objects.create(player1=player1, player2=player2)
            t.save()
        

    def valid_ordering(self, players):
        for player1, player2 in chunk(players, 2):
            if player1.seed == 1 and player2.seed == 1:
                return False
        return True
        
        
        
