def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label=app_label)
        # Reverse order of apps and models.
        app_list = list(reversed(app_list))
        for app in app_list:
            app["models"].sort(key=lambda x: x["name"], reverse=True)
        return app_list