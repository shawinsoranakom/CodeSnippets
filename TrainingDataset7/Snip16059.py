def password_change(self, request, extra_context=None):
        return super().password_change(request, {"spam": "eggs"})