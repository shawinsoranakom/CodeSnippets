def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFeature(handler.feature_external_ges, False)
        self.setFeature(handler.feature_external_pes, False)