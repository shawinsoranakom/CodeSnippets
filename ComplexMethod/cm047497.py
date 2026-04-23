def convert_to_write(self, value, record):
        if isinstance(value, tuple):
            # a tuple of ids, this is the cache format
            value = record.env[self.comodel_name].browse(value)

        if isinstance(value, BaseModel) and value._name == self.comodel_name:
            def get_origin(val):
                return val._origin if isinstance(val, BaseModel) else val

            # make result with new and existing records
            inv_names = {field.name for field in record.pool.field_inverses[self]}
            result = [Command.set([])]
            for record in value:
                origin = record._origin
                if not origin:
                    values = record._convert_to_write({
                        name: record[name]
                        for name in record._cache
                        if name not in inv_names
                    })
                    result.append(Command.create(values))
                else:
                    result[0][2].append(origin.id)
                    if record != origin:
                        values = record._convert_to_write({
                            name: record[name]
                            for name in record._cache
                            if name not in inv_names and get_origin(record[name]) != origin[name]
                        })
                        if values:
                            result.append(Command.update(origin.id, values))
            return result

        if value is False or value is None:
            return [Command.clear()]

        if isinstance(value, list):
            return value

        raise ValueError("Wrong value for %s: %s" % (self, value))