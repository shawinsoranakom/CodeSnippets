def get_column_update(self, record: BaseModel):
        """ Return the value of record in cache as an SQL parameter formatted
        for UPDATE queries.
        """
        field_cache = record.env.transaction.field_data[self]
        record_id = record.id
        if self.company_dependent:
            values = {}
            for ctx_key, cache in field_cache.items():
                if (value := cache.get(record_id, SENTINEL)) is not SENTINEL:
                    values[ctx_key[0]] = self.convert_to_column(value, record)
            return PsycopgJson(values) if values else None
        if self in record.env._field_depends_context:
            # field that will be written to the database depends on context;
            # find the first value that is set
            # If we have more than one value, it is a logical error in the
            # design of the model. In that case, we pick one at random because
            # a stored field can have only one value.
            for ctx_key, cache in field_cache.items():
                if (value := cache.get(record_id, SENTINEL)) is not SENTINEL:
                    break
            else:
                raise AssertionError(f"Value not in cache for field {self} and id={record_id}")
        else:
            value = field_cache[record_id]
        return self.convert_to_column_insert(value, record, validate=False)