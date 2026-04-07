def get_safe_request_meta(self, request):
        """
        Return a dictionary of request.META with sensitive values redacted.
        """
        if not hasattr(request, "META"):
            return {}
        return {k: self.cleanse_setting(k, v) for k, v in request.META.items()}