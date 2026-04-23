def _update_cache(self, records: BaseModel, cache_value: typing.Any, dirty: bool = False) -> None:
        """ Update the value in the cache for the given records, and optionally
        make the field dirty for those records (for stored column fields only).

        One can normally make a clean field dirty but not the other way around.
        Updating a dirty field without ``dirty=True`` is a programming error and
        logs an error.

        :param dirty: whether ``field`` must be made dirty on ``record`` after
            the update
        """
        env = records.env
        field_cache = self._get_cache(env)
        for id_ in records._ids:
            field_cache[id_] = cache_value

        # dirty only makes sense for stored column fields
        if self.column_type and self.store:
            if dirty:
                env._field_dirty[self].update(id_ for id_ in records._ids if id_)
            else:
                dirty_ids = env._field_dirty.get(self)
                if dirty_ids and not dirty_ids.isdisjoint(records._ids):
                    _logger.error(
                        "Field._update_cache() updating the value on %s.%s where dirty flag is already set",
                        records, self.name, stack_info=True,
                    )