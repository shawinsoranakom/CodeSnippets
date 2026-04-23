def _flush(self) -> None:
        # pop dirty fields and their corresponding record ids from cache
        dirty_fields = self.env._field_dirty
        dirty_field_ids = {
            field: ids
            for field in self._fields.values()
            if (ids := dirty_fields.pop(field, None))
        }
        if not dirty_field_ids:
            return

        # for context-dependent fields, `get_column_update` contains the
        # logic to find which value to flush
        model = self

        # sort dirty record ids so that records with the same set of modified
        # fields are grouped together; for that purpose, map each dirty id to
        # an integer that represents its subset of dirty fields (bitmask)
        dirty_ids = sorted(
            OrderedSet(id_ for ids in dirty_field_ids.values() for id_ in ids),
            key=lambda id_: sum(
                1 << field_index
                for field_index, ids in enumerate(dirty_field_ids.values())
                if id_ in ids
            ),
        )

        # perform updates in batches in order to limit memory footprint
        BATCH_SIZE = 1000
        for some_ids in split_every(BATCH_SIZE, dirty_ids):
            vals_list = []
            try:
                for id_ in some_ids:
                    record = model.browse((id_,))
                    vals_list.append({
                        f.name: f.get_column_update(record)
                        for f, ids in dirty_field_ids.items()
                        if id_ in ids
                    })
            except KeyError:
                raise AssertionError(
                    f"Could not find all values of {record} to flush them\n"
                    f"    Context: {self.env.context}\n"
                    f"    Cache: {self.env.cache!r}"
                )
            model.browse(some_ids)._write_multi(vals_list)