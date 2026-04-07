def __get__(self, instance, cls=None):
        """
        Get the related instance through the forward relation.

        With the example above, when getting ``child.parent``:

        - ``self`` is the descriptor managing the ``parent`` attribute
        - ``instance`` is the ``child`` instance
        - ``cls`` is the ``Child`` class (we don't need it)
        """
        if instance is None:
            return self

        # The related instance is loaded from the database and then cached
        # by the field on the model instance state. It can also be pre-cached
        # by the reverse accessor (ReverseOneToOneDescriptor).
        try:
            rel_obj = self.field.get_cached_value(instance)
        except KeyError:
            rel_obj = None
            has_value = None not in self.field.get_local_related_value(instance)
            if has_value:
                model = self.field.model
                for current_instance, ancestor in _traverse_ancestors(model, instance):
                    if ancestor:
                        # The value might be cached on an ancestor if the
                        # instance originated from walking down the inheritance
                        # chain.
                        rel_obj = self.field.get_cached_value(ancestor, default=None)
                        if rel_obj is not None:
                            break

            if rel_obj is None and has_value:
                instance._state.fetch_mode.fetch(self, instance)
                return self.field.get_cached_value(instance)

            self.field.set_cached_value(instance, rel_obj)

        if rel_obj is None and not self.field.null:
            raise self.RelatedObjectDoesNotExist(
                "%s has no %s." % (self.field.model.__name__, self.field.name)
            )
        else:
            return rel_obj