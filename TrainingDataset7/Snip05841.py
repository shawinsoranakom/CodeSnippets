def get_log_entries(self, request):
        from django.contrib.admin.models import LogEntry

        return LogEntry.objects.select_related("content_type", "user")