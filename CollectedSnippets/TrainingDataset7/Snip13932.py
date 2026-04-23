def serve(self, request):
        os_rel_path = self.file_path(request.path)
        os_rel_path = posixpath.normpath(unquote(os_rel_path))
        # Emulate behavior of django.contrib.staticfiles.views.serve() when it
        # invokes staticfiles' finders functionality.
        # TODO: Modify if/when that internal API is refactored
        final_rel_path = os_rel_path.replace("\\", "/").lstrip("/")
        return serve(request, final_rel_path, document_root=self.get_base_dir())