def filter(self, *args, **kwargs):
        queryset = super().filter(fun=True)
        queryset._filter_CustomManager = True
        return queryset