def _prepare(cls):
        """Create some methods once self._meta has been populated."""
        opts = cls._meta
        opts._prepare(cls)

        if opts.order_with_respect_to:
            cls.get_next_in_order = partialmethod(
                cls._get_next_or_previous_in_order, is_next=True
            )
            cls.get_previous_in_order = partialmethod(
                cls._get_next_or_previous_in_order, is_next=False
            )

            # Defer creating accessors on the foreign class until it has been
            # created and registered. If remote_field is None, we're ordering
            # with respect to a GenericForeignKey and don't know what the
            # foreign class is - we'll add those accessors later in
            # contribute_to_class().
            if opts.order_with_respect_to.remote_field:
                wrt = opts.order_with_respect_to
                remote = wrt.remote_field.model
                lazy_related_operation(make_foreign_order_accessors, cls, remote)

        # Give the class a docstring -- its definition.
        if cls.__doc__ is None:
            cls.__doc__ = "%s(%s)" % (
                cls.__name__,
                ", ".join(f.name for f in opts.fields),
            )

        get_absolute_url_override = settings.ABSOLUTE_URL_OVERRIDES.get(
            opts.label_lower
        )
        if get_absolute_url_override:
            setattr(cls, "get_absolute_url", get_absolute_url_override)

        if not opts.managers:
            if any(f.name == "objects" for f in opts.fields):
                raise ValueError(
                    "Model %s must specify a custom Manager, because it has a "
                    "field named 'objects'." % cls.__name__
                )
            manager = Manager()
            manager.auto_created = True
            cls.add_to_class("objects", manager)

        # Set the name of _meta.indexes. This can't be done in
        # Options.contribute_to_class() because fields haven't been added to
        # the model at that point.
        for index in cls._meta.indexes:
            if not index.name:
                index.set_name_with_model(cls)

        class_prepared.send(sender=cls)