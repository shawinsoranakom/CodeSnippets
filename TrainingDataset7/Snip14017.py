def enable(self):
        self.catch_warnings = warnings.catch_warnings()
        self.catch_warnings.__enter__()
        self.filter_func("ignore", **self.ignore_kwargs)