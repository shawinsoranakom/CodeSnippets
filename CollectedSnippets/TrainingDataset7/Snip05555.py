def _check_view_on_site_url(self, obj):
        if not callable(obj.view_on_site) and not isinstance(obj.view_on_site, bool):
            return [
                checks.Error(
                    "The value of 'view_on_site' must be a callable or a boolean "
                    "value.",
                    obj=obj.__class__,
                    id="admin.E025",
                )
            ]
        else:
            return []