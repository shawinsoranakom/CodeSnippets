def get_log_entries(self, request):
        from django.contrib.contenttypes.models import ContentType

        log_entries = super().get_log_entries(request)
        return log_entries.filter(
            content_type__in=ContentType.objects.get_for_models(
                *self._registry.keys()
            ).values()
        )