from django.views.generic import simple
from django.conf import settings

default_whitelist = (
    '127.0.0',
    '209.113.164.',)

class BlockUnknown(object):
    def process_request(self, request):
        ip = request.META['REMOTE_ADDR']
        allowed_ip_matches = getattr(settings, 'REMOTE_WHITELIST',
                                     default_whitelist)
        for ip_match in allowed_ip_matches:
            if ip.startswith(ip_match):
                return None
        return simple.direct_to_template(request, template='blocked.html')
