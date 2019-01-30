

def applications(request):

    from janus.models import ApplicationExtension
    objects = ApplicationExtension.objects.filter(display_name__isnull=False)

    ret = []

    for o in objects:
        ret.append({'name': o.display_name, 'url': o.link})
    return {
        'APPLICATIONS': ret,
    }