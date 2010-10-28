import datetime
import itertools
import math
from django.db import models
from mynonrel import fields
from django.core.cache import cache
from django.contrib.auth.models import User

from cachehelper.helper import cachelib

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

    def set_teams(self, teams):
        cache.set("player_%s_teams" % self.pk, teams, 86400)

    @cachelib.register_cache("pteams", cache_timeout=3600)
    def get_teams(self):
        results = cache.get("player_%s_teams" % self.pk)
        if results is not None:
            return results
        teams = []
        for team in Team.objects.all():
            if team.player1 == self or team.player2 == self:
                teams.append(team)
        teams.sort(key=lambda t: 0 if t.player2 is None else 1)
        return teams


class Tournament(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

    @cachelib.register_cache("tdivisions")
    def get_divisions(self):
        d = list(Division.objects.filter(tournament = self))
        d.sort(key = lambda x: x.pk)
        singles_divisions = []
        doubles_divisions = []
        for division in d:
            if not division.teams:
                continue
            for team in division.teams:
                str(team.player1)
                str(team.player2)
            if division.is_double():
                doubles_divisions.append(division)
            else:
                singles_divisions.append(division)
        return singles_divisions, doubles_divisions


GAME_TYPES = (
('single', 'single'),
('double', 'double'),
)

class Team(models.Model):
    player1 = models.ForeignKey(Player, related_name='player1_set')
    player2 = models.ForeignKey(Player, related_name='player2_set', blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        if not self.player2:
            return self.player1.__unicode__()
        if self.name:
            return self.name
        else:
            template = 'Team %(players)s'
        players = [self.player1]
        if self.player2:
            players.append(self.player2)
        return template % {'name': self.name,
                           'players': ' and '.join(map(str, players))}

    @models.permalink
    def get_absolute_url(self):
        return ('view-team', (self.pk,), {})

    def stats_key(self):
        return 'stats__%s' % self.pk        

    @cachelib.register_cache("stats")
    def stats(self, allow_cache=True):
        team = self
        games = list(Match.objects.filter(team1=team))
        games += list(Match.objects.filter(team2=team))
        wins, losses = 0, 0
        for game in games:
            winner = game.winner()
            if winner is not None:
                if winner == team:
                    wins += 1
                else:
                    losses += 1
        return (wins, losses, games)

    def save(self, *args, **kwargs):
        super(Team, self).save(*args, **kwargs)
        divisions = Division.objects.all()
        t = set()
        for d in divisions:
            if self.pk in d.teams_data:
                cachelib.recalculate(d)
                t.add(d.tournament)
        for tournament in t:
            cachelib.recalculate(tournament)

    @cachelib.register_cache("matches")
    def matches(self):
        team = self
        def dvl(x, d):
            if x is None:
                return d
            else:
                return x
        wins, losses, matches = self.stats()
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
        
        return historical, future

class Division(models.Model):
    teams = fields.RelListField(models.ForeignKey(Team))
    tournament = models.ForeignKey(Tournament)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return u"Division '%s' for %s" % (self.name, self.tournament)

    def is_double(self):
        return bool(self.teams[0].player2)

    def save(self, *args, **kwargs):
        super(Division, self).save(*args, **kwargs)
        cachelib.recalculate(self.tournament)
        cachelib.recalculate(self)

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
        super(Match, self).save(*args, **kwargs)
        cachelib.recalculate(self.team1)
        cachelib.recalculate(self.team2)

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


    def winner(self):
        if self.team1_scores is None:
            return None
        score_wins = [(a > b) - (a < b) for a, b in zip(self.team1_scores, self.team2_scores)]
        if sum(score_wins) == 0:
            return None
        elif sum(score_wins) > 0:
            return self.team1
        else:
            return self.team2
