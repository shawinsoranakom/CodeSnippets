def change_view(self, *args, **kwargs):
        kwargs["extra_context"] = {"show_delete": False}
        return super().change_view(*args, **kwargs)