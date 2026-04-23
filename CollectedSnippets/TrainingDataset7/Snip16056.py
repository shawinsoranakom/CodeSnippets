def index(self, request, extra_context=None):
        return super().index(request, {"foo": "*bar*"})