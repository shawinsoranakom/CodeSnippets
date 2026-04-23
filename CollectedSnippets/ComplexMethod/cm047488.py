def __get__(self, records: BaseModel, owner=None):
        # base case: do the regular access
        if records is None or len(records._ids) <= 1:
            return super().__get__(records, owner)

        records._check_field_access(self, 'read')

        # multi-record case
        if self.compute and self.store:
            self.recompute(records)

        # get the cache
        env = records.env
        field_cache = self._get_cache(env)

        # retrieve values in cache, and fetch missing ones
        vals = []
        for record_id in records._ids:
            try:
                vals.append(field_cache[record_id])
            except KeyError:
                if self.store and record_id and len(vals) < len(records) - PREFETCH_MAX:
                    # a lot of missing records, just fetch that field
                    remaining = records[len(vals):]
                    remaining.fetch([self.name])
                    # fetch does not raise MissingError, check value
                    if record_id not in field_cache:
                        raise MissingError("\n".join([
                            env._("Record does not exist or has been deleted."),
                            env._("(Record: %(record)s, User: %(user)s)", record=record_id, user=env.uid),
                        ])) from None
                else:
                    remaining = records.__class__(env, (record_id,), records._prefetch_ids)
                    super().__get__(remaining, owner)
                # we have the record now
                vals.append(field_cache[record_id])

        return self.convert_to_record_multi(vals, records)