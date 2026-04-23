def __init__(self, **kwargs):
        self.ignore_kwargs = kwargs
        if "message" in self.ignore_kwargs or "module" in self.ignore_kwargs:
            self.filter_func = warnings.filterwarnings
        else:
            self.filter_func = warnings.simplefilter
        super().__init__()