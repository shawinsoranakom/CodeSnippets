def convert_to_cache(self, value, record, validate=True):
        # cache format: id or None
        if type(value) is int or type(value) is NewId:
            id_ = value
        elif isinstance(value, BaseModel):
            if validate and (value._name != self.comodel_name or len(value) > 1):
                raise ValueError("Wrong value for %s: %r" % (self, value))
            id_ = value._ids[0] if value._ids else None
        elif isinstance(value, tuple):
            # value is either a pair (id, name), or a tuple of ids
            id_ = value[0] if value else None
        elif isinstance(value, dict):
            # return a new record (with the given field 'id' as origin)
            comodel = record.env[self.comodel_name]
            origin = comodel.browse(value.get('id'))
            id_ = comodel.new(value, origin=origin).id
        else:
            id_ = None

        if self.delegate and record and not any(record._ids):
            # if all records are new, then so is the parent
            id_ = id_ and NewId(id_)

        return id_