import math
from django.db import models
from mynonrel import fields

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

class Division(models.Model):
    teams = fields.RelListField(models.ForeignKey(Team))
    tournament = models.ForeignKey(Tournament)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return u"Division '%s' for %s" % (self.name, self.tournament)


BEST_OF = (
    (1, 1),
    (3, 3),
    (5, 5),
    (7, 7),
)


class Match(models.Model):
    match_type = models.CharField(choices=GAME_TYPES, max_length=255, default='single', blank=True)
    team1 = models.ForeignKey(Team, related_name='team1_set')
    team2 = models.ForeignKey(Team, related_name='team2_set')
    played = models.DateField(blank=True, null=True)
    num_games = models.IntegerField(blank=True, null=True, verbose_name="Number of games")
    best_of = models.IntegerField(choices=BEST_OF, default=3)
    parent_game = models.ForeignKey('self', blank=True, null=True)
    parent_division = models.ForeignKey(Division, blank=True, null=True)
    team1_scores = fields.RelListField(models.IntegerField(), blank=True, null=True)
    team2_scores = fields.RelListField(models.IntegerField(), blank=True, null=True)
    score_recorded = models.DateTimeField(blank=True, null=True)
    score_recorded_by = models.ForeignKey(User, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Matches'

    def save(self, *args, **kwargs):

        return super(Match, self).save(*args, **kwargs)

    def __unicode__(self):
        return "Match between %s and %s" % (self.team1, self.team2)

    def clean(self):
        from django.core.exceptions import ValidationError
        if bool(self.team1.player2) ^ bool(self.team2.player2):
            raise ValidationError("Cannot match a single versus a double!")
        if self.team1.player2:
            self.match_type = 'doubles'
        else:
            self.match_type = 'singles'
        if self.team1.player1 == self.team2.player1:
            raise ValidationError("Player %s cannot play himself!" % self.team1.player1)
        if self.match_type == 'doubles':
            if self.team1.player1 == self.team2.player2:
                raise ValidationError("Player %s cannot play himself!" % self.team1.player1)
            if self.team1.player2 == self.team2.player1:
                raise ValidationError("Player %s cannot play himself!" % self.team1.player2)
            if self.team1.player2 == self.team2.player2:
                raise ValidationError("Player %s cannot play himself!" % self.team1.player2)
        if self.num_games is not None:
            min_allowed = int(math.ceil(self.best_of / 2.0))
            max_allowed = self.best_of
            if self.num_games < min_allowed or self.num_games > max_allowed:
                raise ValidationError("Number of games should be between %s and %s" % (min_allowed, max_allowed))
            if len(self.team1_scores) != self.num_games or len(self.team2_scores) != self.num_games:
                raise ValidationError("Number of games does not match number of scores.")
        if len(self.team1_scores) != len(self.team2_scores):
            raise ValidationError("Score lengths do not match.")

