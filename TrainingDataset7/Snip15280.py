def get_urls(self):
        # Add the URL of our custom 'add_view' view to the front of the URLs
        # list. Remove the existing one(s) first
        from django.urls import re_path

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        info = self.opts.app_label, self.opts.model_name

        view_name = "%s_%s_add" % info

        return [
            re_path("^!add/$", wrap(self.add_view), name=view_name),
        ] + self.remove_url(view_name)