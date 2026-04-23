def _remove_inverses(self, records: BaseModel, value):
        """ Remove `records` from the cached values of the inverse fields (o2m) of `self`. """
        inverse_fields = records.pool.field_inverses[self]
        if not inverse_fields:
            return

        record_ids = set(records._ids)
        # align(id) returns a NewId if records are new, a real id otherwise
        align = (lambda id_: id_) if all(record_ids) else (lambda id_: id_ and NewId(id_))
        field_cache = self._get_cache(records.env)
        corecords = records.env[self.comodel_name].browse(
            align(coid) for record_id in records._ids
            if (coid := field_cache.get(record_id)) is not None
        )

        for invf in inverse_fields:
            inv_cache = invf._get_cache(corecords.env)
            for corecord in corecords:
                ids0 = inv_cache.get(corecord.id)
                if ids0 is not None:
                    ids1 = tuple(id_ for id_ in ids0 if id_ not in record_ids)
                    invf._update_cache(corecord, ids1)