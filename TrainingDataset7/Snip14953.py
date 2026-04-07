def get(self, request, *args, **kwargs):
        self.object = None
        return super().get(request, *args, **kwargs)