def __set__(self, records: BaseModel, value) -> None:
        """ set the value of field ``self`` on ``records`` """
        protected_ids = []
        new_ids = []
        other_ids = []
        for record_id in records._ids:
            if record_id in records.env._protected.get(self, ()):
                protected_ids.append(record_id)
            elif not record_id:
                new_ids.append(record_id)
            else:
                other_ids.append(record_id)

        if protected_ids:
            # records being computed: no business logic, no recomputation
            protected_records = records.__class__(records.env, tuple(protected_ids), records._prefetch_ids)
            self.write(protected_records, value)

        if new_ids:
            # new records: no business logic
            new_records = records.__class__(records.env, tuple(new_ids), records._prefetch_ids)
            with records.env.protecting(records.pool.field_computed.get(self, [self]), new_records):
                if self.relational:
                    new_records.modified([self.name], before=True)
                self.write(new_records, value)
                new_records.modified([self.name])

            if self.inherited:
                # special case: also assign parent records if they are new
                parents = new_records[self.related.split('.')[0]]
                parents.filtered(lambda r: not r.id)[self.name] = value

        if other_ids:
            # base case: full business logic
            records = records.__class__(records.env, tuple(other_ids), records._prefetch_ids)
            write_value = self.convert_to_write(value, records)
            records.write({self.name: write_value})