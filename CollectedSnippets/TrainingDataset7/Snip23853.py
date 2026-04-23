def get(self, request, *args, **kwargs):
        # Ensures get_context_object_name() doesn't reference self.object.
        author = self.get_object()
        context = {"custom_" + self.get_context_object_name(author): author}
        return self.render_to_response(context)