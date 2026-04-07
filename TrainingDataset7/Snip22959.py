def __init__(self, *args, custom_kwarg, **kwargs):
        self.custom_kwarg = custom_kwarg
        super().__init__(*args, **kwargs)