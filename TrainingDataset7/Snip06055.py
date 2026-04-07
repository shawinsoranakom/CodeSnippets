def lookup_allowed(self, lookup, value, request):
        # Don't allow lookups involving passwords.
        return not lookup.startswith("password") and super().lookup_allowed(
            lookup, value, request
        )