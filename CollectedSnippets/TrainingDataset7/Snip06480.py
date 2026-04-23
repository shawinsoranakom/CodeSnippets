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
        opts = self.model._meta
        self.instance = instance
        self.rel_name = (
            opts.app_label
            + "-"
            + opts.model_name
            + "-"
            + self.ct_field.name
            + "-"
            + self.ct_fk_field.name
        )
        self.save_as_new = save_as_new
        if self.instance is None or not self.instance._is_pk_set():
            qs = self.model._default_manager.none()
        else:
            if queryset is None:
                queryset = self.model._default_manager
            qs = queryset.filter(
                **{
                    self.ct_field.name: ContentType.objects.get_for_model(
                        self.instance, for_concrete_model=self.for_concrete_model
                    ),
                    self.ct_fk_field.name: self.instance.pk,
                }
            )
        super().__init__(queryset=qs, data=data, files=files, prefix=prefix, **kwargs)