def _set_queryset(self, queryset):
        self._queryset = None if queryset is None else queryset.all()
        self.widget.choices = self.choices