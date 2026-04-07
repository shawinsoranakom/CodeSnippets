def get_check_kwargs(self, options):
        kwargs = super().get_check_kwargs(options)
        return {**kwargs, "databases": [options["database"]]}