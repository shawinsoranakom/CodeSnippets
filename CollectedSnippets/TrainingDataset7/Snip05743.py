def log_addition(self, request, obj, message):
        """
        Log that an object has been successfully added.

        The default implementation creates an admin LogEntry object.
        """
        from django.contrib.admin.models import ADDITION, LogEntry

        return LogEntry.objects.log_actions(
            user_id=request.user.pk,
            queryset=[obj],
            action_flag=ADDITION,
            change_message=message,
            single_object=True,
        )