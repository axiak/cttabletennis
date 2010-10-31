from django import template
register = template.Library()

places = (
    ('home', ''),
    'teams',
   ('players', 'tournament/players/'),
    ('divisions', 'tournament/divisions/'),
    'rules',
    
#    'brackets',
    'prizes',
)

@register.inclusion_tag("nav/nav_header.html", takes_context=True)
def nav_header(context):
    path = None
    if 'REQUEST_PATH' in context:
        path = context['REQUEST_PATH'].strip('/')
    place_list = []
    for place in places:
        if isinstance(place, basestring):
            place_list.append((place, place))
        else:
            place_list.append(place)
    for place in places:
        if isinstance(place, basestring):
            place = (place, place)
        place, url = place
        if path == url.strip('/'):
            break
    else:
        place = None
    return {'places': place_list,
            'current_place': place}

    
