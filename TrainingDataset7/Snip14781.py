def get_safe_cookies(self, request):
        """
        Return a dictionary of request.COOKIES with sensitive values redacted.
        """
        if not hasattr(request, "COOKIES"):
            return {}
        return {k: self.cleanse_setting(k, v) for k, v in request.COOKIES.items()}