def serve(self, request):
        """Serve the request path."""
        return serve(request, self.file_path(request.path), insecure=True)