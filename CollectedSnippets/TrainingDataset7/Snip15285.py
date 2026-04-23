def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)