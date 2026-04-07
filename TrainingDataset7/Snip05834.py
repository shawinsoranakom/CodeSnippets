def login(self, request, extra_context=None):
        """
        Display the login form for the given HttpRequest.
        """
        # Since this module gets imported in the application's root package,
        # it cannot import models from other applications at the module level,
        # and django.contrib.admin.forms eventually imports User.
        from django.contrib.admin.forms import AdminAuthenticationForm
        from django.contrib.auth.views import LoginView

        redirect_url = LoginView().get_redirect_url(request) or reverse(
            "admin:index", current_app=self.name
        )
        if request.method == "GET" and self.has_permission(request):
            # Already logged-in, redirect accordingly.
            return HttpResponseRedirect(redirect_url)

        context = {
            **self.each_context(request),
            "title": _("Log in"),
            "subtitle": None,
            "app_path": request.get_full_path(),
            "username": request.user.get_username(),
            REDIRECT_FIELD_NAME: redirect_url,
        }
        context.update(extra_context or {})

        defaults = {
            "extra_context": context,
            "authentication_form": self.login_form or AdminAuthenticationForm,
            "template_name": self.login_template or "admin/login.html",
        }
        request.current_app = self.name
        return LoginView.as_view(**defaults)(request)