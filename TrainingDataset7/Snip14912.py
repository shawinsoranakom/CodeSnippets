def uses_datetime_field(self):
        """
        Return `True` if the date field is a `DateTimeField` and `False`
        if it's a `DateField`.
        """
        model = self.get_queryset().model if self.model is None else self.model
        field = model._meta.get_field(self.get_date_field())
        return isinstance(field, models.DateTimeField)