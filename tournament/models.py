from django.db import models
from djangotoolbox import fields

from django.contrib.auth.models import User

__all__ = ('Player', 'Tournament', 'Division', 'Match', 'Team')


class Player(models.Model):
    user = models.ForeignKey(User, unique=True)
    wins = models.IntegerField(blank=True, null=True)
    losses = models.IntegerField(blank=True, null=True)
    nickname = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    seed = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        if self.user.first_name or self.user.last_name:
            template = u'%s%%s %s' % (self.user.first_name, self.user.last_name)
        else:
            template = u'%s%%s' % self.user.username

        if self.nickname:
            n = u' "%s"' % self.nickname
        else:
            n = u''
        return template % n


class Tournament(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Division(models.Model):
    players = fields.ListField(models.ForeignKey(Player))
    tournament = models.ForeignKey(Tournament)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return u"Division '%s' for %s" % (self.name, self.tournament)


GAME_TYPES = (
('single', 'single'),
('double', 'double'),
)

class Team(models.Model):
    player1 = models.ForeignKey(Player, related_name='player1_set')
    player2 = models.ForeignKey(Player, related_name='player2_set', blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        if self.name:
            template = '%(name)s (%(players)s)'
        else:
            template = 'Team %(players)s'
        players = [self.player1]
        if self.player2:
            players.append(self.player2)
        return template % {'name': self.name,
                           'players': ' and '.join(map(str, players))}

class Match(models.Model):
    match_type = models.CharField(choices=GAME_TYPES, max_length=255, default='single')
    team1 = models.ForeignKey(Team, related_name='team1_set')
    team2 = models.ForeignKey(Team, related_name='team2_set')
    played = models.DateField(blank=True, null=True)
    num_games = models.IntegerField(blank=True, null=True)
    parent_game = models.ForeignKey('self', blank=True, null=True)
    parent_division = models.ForeignKey(Division, blank=True, null=True)
    team1_scores = fields.ListField(models.IntegerField(blank=True, null=True))
    team2_scores = fields.ListField(models.IntegerField(blank=True, null=True))

    class Meta:
        verbose_name_plural = 'Matches'

    def __unicode__(self):
        return "Match between %s and %s" % (self.team1, self.team2)

