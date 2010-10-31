

def msie_processor(request):
    if 'MSIE' in request.META.get('HTTP_USER_AGENT', '').split():
        return {'MSIE': True}
    else:
        return {'MSIE': False}
