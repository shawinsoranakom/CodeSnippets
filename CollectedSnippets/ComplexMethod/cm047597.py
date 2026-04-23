def mapped(self, func: str | Callable[[Self], T]) -> list | BaseModel:
        """Apply ``func`` on all records in ``self``, and return the result as a
        list or a recordset (if ``func`` return recordsets). In the latter
        case, the order of the returned recordset is arbitrary.

        :param func: a function or a dot-separated sequence of field names
        :return: self if func is falsy, result of func applied to all ``self`` records.

        .. code-block:: python3

            # returns a list of summing two fields for each record in the set
            records.mapped(lambda r: r.field1 + r.field2)

        The provided function can be a string to get field values:

        .. code-block:: python3

            # returns a list of names
            records.mapped('name')

            # returns a recordset of partners
            records.mapped('partner_id')

            # returns the union of all partner banks, with duplicates removed
            records.mapped('partner_id.bank_ids')
        """
        if not func:
            return self                 # support for an empty path of fields

        if isinstance(func, str):
            # special case: sequence of field names
            *rel_field_names, field_name = func.split('.')
            records = self
            for rel_field_name in rel_field_names:
                records = records[rel_field_name]
            if len(records) > PREFETCH_MAX:
                # fetch fields for all recordset in case we have a recordset
                # that is larger than the prefetch
                records.fetch([field_name])
            field = records._fields[field_name]
            getter = field.__get__
            if field.relational:
                # union of records
                return getter(records)
            return [getter(record) for record in records]

        if self:
            vals = [func(rec) for rec in self]
            if isinstance(vals[0], BaseModel):
                return vals[0].union(*vals)
            return vals
        else:
            # we want to follow-up the comodel from the function
            # so we pass an empty recordset
            vals = func(self)
            return vals if isinstance(vals, BaseModel) else []