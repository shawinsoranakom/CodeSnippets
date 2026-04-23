def process_view(self, request, view_func, view_args, view_kwargs):
        if not getattr(view_func, "login_required", True):
            return None

        if request.user.is_authenticated:
            return None

        return self.handle_no_permission(request, view_func)