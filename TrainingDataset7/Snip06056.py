def add_view(self, request, form_url="", extra_context=None):
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return self._add_view(request, form_url, extra_context)

        with transaction.atomic(using=router.db_for_write(self.model)):
            return self._add_view(request, form_url, extra_context)