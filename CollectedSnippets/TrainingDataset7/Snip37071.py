def raises403(request):
    raise PermissionDenied("Insufficient Permissions")