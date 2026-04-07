def dispatch(self, request, *args, **kwargs):
                assert hasattr(self, "attr")
                return super().dispatch(request, *args, **kwargs)