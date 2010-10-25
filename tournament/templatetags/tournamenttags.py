from django import template
register = template.Library()
from tournament.models import *


@register.inclusion_tag("tournament/team_item_include.html")
def team_item(team):
    wins, losses, games = team.stats()
    return {'team': team,
            'wins': wins,
            'losses': losses}
