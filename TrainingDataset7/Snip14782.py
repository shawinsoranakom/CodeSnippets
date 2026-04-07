def is_active(self, request):
        """
        This filter is to add safety in production environments (i.e. DEBUG
        is False). If DEBUG is True then your site is not safe anyway.
        This hook is provided as a convenience to easily activate or
        deactivate the filter on a per request basis.
        """
        return settings.DEBUG is False