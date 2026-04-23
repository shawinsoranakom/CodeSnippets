def __init__(
        self,
        data=None,
        files=None,
        instance=None,
        save_as_new=False,
        prefix=None,
        queryset=None,
        **kwargs,
    ):
        if instance is None:
            self.instance = self.fk.remote_field.model()
        else:
            self.instance = instance
        self.save_as_new = save_as_new
        if queryset is None:
            queryset = self.model._default_manager
        if self.instance._is_pk_set():
            qs = queryset.filter(**{self.fk.name: self.instance})
        else:
            qs = queryset.none()
        self.unique_fields = {self.fk.name}
        super().__init__(data, files, prefix=prefix, queryset=qs, **kwargs)

        # Add the inline foreign key field to form._meta.fields if it's defined
        # to make sure validation isn't skipped on that field.
        if self.form._meta.fields and self.fk.name not in self.form._meta.fields:
            self.form._meta.fields = list(self.form._meta.fields)
            self.form._meta.fields.append(self.fk.name)