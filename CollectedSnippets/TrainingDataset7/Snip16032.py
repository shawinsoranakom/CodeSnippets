def get_urls(self):
        # Disable change_view, but leave other urls untouched
        urlpatterns = super().get_urls()
        return [p for p in urlpatterns if p.name and not p.name.endswith("_change")]