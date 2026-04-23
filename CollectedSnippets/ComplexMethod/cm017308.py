def in_bulk(self, id_list=None, *, field_name="pk"):
        """
        Return a dictionary mapping each of the given IDs to the object with
        that ID. If `id_list` isn't provided, evaluate the entire QuerySet.
        """
        if self.query.is_sliced:
            raise TypeError("Cannot use 'limit' or 'offset' with in_bulk().")
        if id_list is not None and not id_list:
            return {}
        opts = self.model._meta
        unique_fields = [
            constraint.fields[0]
            for constraint in opts.total_unique_constraints
            if len(constraint.fields) == 1
        ]
        if (
            field_name != "pk"
            and not opts.get_field(field_name).unique
            and field_name not in unique_fields
            and self.query.distinct_fields != (field_name,)
        ):
            raise ValueError(
                "in_bulk()'s field_name must be a unique field but %r isn't."
                % field_name
            )

        qs = self

        def get_obj(obj):
            return obj

        if issubclass(self._iterable_class, ModelIterable):
            # Raise an AttributeError if field_name is deferred.
            get_key = operator.attrgetter(field_name)

        elif issubclass(self._iterable_class, ValuesIterable):
            if field_name not in self.query.values_select:
                qs = qs.values(field_name, *self.query.values_select)

                def get_obj(obj):  # noqa: F811
                    # We can safely mutate the dictionaries returned by
                    # ValuesIterable here, since they are limited to the scope
                    # of this function, and get_key runs before get_obj.
                    del obj[field_name]
                    return obj

            get_key = operator.itemgetter(field_name)

        elif issubclass(self._iterable_class, ValuesListIterable):
            try:
                field_index = self.query.values_select.index(field_name)
            except ValueError:
                # field_name is missing from values_select, so add it.
                field_index = 0
                if issubclass(self._iterable_class, NamedValuesListIterable):
                    kwargs = {"named": True}
                else:
                    kwargs = {}
                    get_obj = operator.itemgetter(slice(1, None))
                qs = qs.values_list(field_name, *self.query.values_select, **kwargs)

            get_key = operator.itemgetter(field_index)

        elif issubclass(self._iterable_class, FlatValuesListIterable):
            if self.query.values_select == (field_name,):
                # Mapping field_name to itself.
                get_key = get_obj
            else:
                # Transform it back into a non-flat values_list().
                qs = qs.values_list(field_name, *self.query.values_select)
                get_key = operator.itemgetter(0)
                get_obj = operator.itemgetter(1)

        else:
            raise TypeError(
                f"in_bulk() cannot be used with {self._iterable_class.__name__}."
            )

        if id_list is not None:
            filter_key = "{}__in".format(field_name)
            id_list = tuple(id_list)
            batch_size = connections[self.db].ops.bulk_batch_size([opts.pk], id_list)
            # If the database has a limit on the number of query parameters
            # (e.g. SQLite), retrieve objects in batches if necessary.
            if batch_size and batch_size < len(id_list):
                results = ()
                for offset in range(0, len(id_list), batch_size):
                    batch = id_list[offset : offset + batch_size]
                    results += tuple(qs.filter(**{filter_key: batch}))
                qs = results
            else:
                qs = qs.filter(**{filter_key: id_list})
        else:
            qs = qs._chain()
        return {get_key(obj): get_obj(obj) for obj in qs}