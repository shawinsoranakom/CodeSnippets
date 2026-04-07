def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)