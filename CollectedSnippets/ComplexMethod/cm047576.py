def _determine_fields_to_fetch(
            self,
            field_names: Collection[str] | None = None,
            ignore_when_in_cache: bool = False,
        ) -> list[Field]:
        """
        Return the fields to fetch from database among the given field names,
        and following the dependencies of computed fields. The method is used
        by :meth:`fetch` and :meth:`search_fetch`.

        :param field_names: the collection of requested fields, or ``None`` for
            all accessible fields marked with ``prefetch=True``
        :param ignore_when_in_cache: whether to ignore fields that are alreay in cache for ``self``
        :return: the list of fields that must be fetched
        :raise AccessError: when trying to fetch fields to which the user does not have access
        """
        if field_names is None:
            return [
                field
                for field in self._fields.values()
                if field.prefetch is True and self._has_field_access(field, 'read')
            ]

        if not field_names:
            return []

        fields_to_fetch: list[Field] = []
        fields_todo = deque[Field]()
        fields_done = {self._fields['id']}  # trick: ignore 'id'
        for field_name in field_names:
            try:
                field = self._fields[field_name]
            except KeyError as e:
                raise ValueError(f"Invalid field {field_name!r} on {self._name!r}") from e
            self._check_field_access(field, 'read')
            fields_todo.append(field)

        while fields_todo:
            field = fields_todo.popleft()
            if field in fields_done:
                continue
            fields_done.add(field)
            if ignore_when_in_cache and not any(field._cache_missing_ids(self)):
                # field is already in cache: don't fetch it
                continue
            if field.store:
                fields_to_fetch.append(field)
            else:
                # optimization: fetch field dependencies
                for dotname in self.pool.field_depends[field]:
                    dep_field = self._fields[dotname.split('.', 1)[0]]
                    if (not dep_field.store) or (
                        dep_field.prefetch is True
                        and self._has_field_access(dep_field, 'read')
                    ):
                        fields_todo.append(dep_field)

        return fields_to_fetch