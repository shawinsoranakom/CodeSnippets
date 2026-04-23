def __set__(self, instance, value):
        """
        Set the related instance through the reverse relation.

        With the example above, when setting ``place.restaurant = restaurant``:

        - ``self`` is the descriptor managing the ``restaurant`` attribute
        - ``instance`` is the ``place`` instance
        - ``value`` is the ``restaurant`` instance on the right of the equal
          sign

        Keep in mind that ``Restaurant`` holds the foreign key to ``Place``.
        """
        # The similarity of the code below to the code in
        # ForwardManyToOneDescriptor is annoying, but there's a bunch
        # of small differences that would make a common base class convoluted.

        if value is None:
            # Update the cached related instance (if any) & clear the cache.
            # Following the example above, this would be the cached
            # ``restaurant`` instance (if any).
            rel_obj = self.related.get_cached_value(instance, default=None)
            if rel_obj is not None:
                # Remove the ``restaurant`` instance from the ``place``
                # instance cache.
                self.related.delete_cached_value(instance)
                # Set the ``place`` field on the ``restaurant``
                # instance to None.
                setattr(rel_obj, self.related.field.name, None)
        elif not isinstance(value, self.related.related_model):
            # An object must be an instance of the related class.
            raise ValueError(
                'Cannot assign "%r": "%s.%s" must be a "%s" instance.'
                % (
                    value,
                    instance._meta.object_name,
                    self.related.accessor_name,
                    self.related.related_model._meta.object_name,
                )
            )
        else:
            if instance._state.db is None:
                instance._state.db = router.db_for_write(
                    instance.__class__, instance=value
                )
            if value._state.db is None:
                value._state.db = router.db_for_write(
                    value.__class__, instance=instance
                )
            if not router.allow_relation(value, instance):
                raise ValueError(
                    'Cannot assign "%r": the current database router prevents this '
                    "relation." % value
                )

            related_pk = tuple(
                getattr(instance, field.attname)
                for field in self.related.field.foreign_related_fields
            )
            # Set the value of the related field to the value of the related
            # object's related field.
            for index, field in enumerate(self.related.field.local_related_fields):
                setattr(value, field.attname, related_pk[index])

            # Set the related instance cache used by __get__ to avoid an SQL
            # query when accessing the attribute we just set.
            self.related.set_cached_value(instance, value)

            # Set the forward accessor cache on the related object to the
            # current instance to avoid an extra SQL query if it's accessed
            # later on.
            self.related.field.set_cached_value(value, instance)