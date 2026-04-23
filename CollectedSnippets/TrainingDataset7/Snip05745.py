def log_deletions(self, request, queryset):
        """
        Log that objects will be deleted. Note that this method must be called
        before the deletion.

        The default implementation creates admin LogEntry objects.
        """
        from django.contrib.admin.models import DELETION, LogEntry

        return LogEntry.objects.log_actions(
            user_id=request.user.pk,
            queryset=queryset,
            action_flag=DELETION,
        )