def __init__(self, *args, renderer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = renderer or get_default_renderer()