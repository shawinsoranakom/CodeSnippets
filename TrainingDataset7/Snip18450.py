def log_change(self, request, obj, message):
        # LogEntry.user column doesn't get altered to expect a UUID, so set an
        # integer manually to avoid causing an error.
        original_pk = request.user.pk
        request.user.pk = 1
        super().log_change(request, obj, message)
        request.user.pk = original_pk