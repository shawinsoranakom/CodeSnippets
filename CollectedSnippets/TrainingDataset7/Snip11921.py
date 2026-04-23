def __enter__(self):
        return self.queryset._disable_cloning()