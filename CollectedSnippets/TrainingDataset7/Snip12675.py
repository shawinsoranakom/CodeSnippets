def __bool__(self):
        return self.field.empty_label is not None or self.queryset.exists()