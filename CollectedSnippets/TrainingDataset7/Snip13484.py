def __init__(self, engine, loaders):
        self.get_template_cache = {}
        self.loaders = engine.get_template_loaders(loaders)
        super().__init__(engine)