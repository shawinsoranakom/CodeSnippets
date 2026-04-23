def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return self._changeform_view(request, object_id, form_url, extra_context)

        with transaction.atomic(using=router.db_for_write(self.model)):
            return self._changeform_view(request, object_id, form_url, extra_context)