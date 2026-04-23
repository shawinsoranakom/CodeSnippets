def dispatch(self, request, *args, **kwargs):
        if not utils.docutils_is_available:
            # Display an error message for people without docutils
            self.template_name = "admin_doc/missing_docutils.html"
            return self.render_to_response(admin.site.each_context(request))
        return super().dispatch(request, *args, **kwargs)