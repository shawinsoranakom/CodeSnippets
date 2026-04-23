def _check_callback(self):
        from django.views import View

        view = self.callback
        if inspect.isclass(view) and issubclass(view, View):
            return [
                Error(
                    "Your URL pattern %s has an invalid view, pass %s.as_view() "
                    "instead of %s."
                    % (
                        self.pattern.describe(),
                        view.__name__,
                        view.__name__,
                    ),
                    id="urls.E009",
                )
            ]
        return []