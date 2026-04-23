def tz(request):
    from django.utils import timezone

    return {"TIME_ZONE": timezone.get_current_timezone_name()}