def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            wrapper.admin_site = self
            # Used by LoginRequiredMiddleware.
            wrapper.login_url = reverse_lazy("admin:login", current_app=self.name)
            return update_wrapper(wrapper, view)