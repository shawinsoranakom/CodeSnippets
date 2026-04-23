def staff_only_view(request):
    """
    A view that can only be visited by staff. Non staff members get an
    exception
    """
    if request.user.is_staff:
        return HttpResponse()
    else:
        raise CustomTestException()