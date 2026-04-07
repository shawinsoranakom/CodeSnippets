def delete_view(self, request, object_id, extra_context=None):
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return self._delete_view(request, object_id, extra_context)

        with transaction.atomic(using=router.db_for_write(self.model)):
            return self._delete_view(request, object_id, extra_context)