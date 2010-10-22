from django.conf import settings

class DebugIp(object):
    def process_request(self, request):
        request._old_debug = settings.DEBUG
        ip = request.META['REMOTE_ADDR']
        if ip.startswith('127.'):
            settings.DEBUG = True
        return None

    def process_response(self, request, response):
        if hasattr(request, '_old_debug'):
            settings.DEBUG = request._old_debug
        return response
