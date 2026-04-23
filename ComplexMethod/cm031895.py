def from_data(cls, raw, index):
        name = raw.name if raw.name else index
        vartype = size = None
        if type(raw.data) is int:
            size = raw.data
        elif isinstance(raw.data, str):
            size = int(raw.data)
        elif raw.data:
            vartype = dict(raw.data)
            del vartype['storage']
            if 'size' in vartype:
                size = vartype.pop('size')
                if isinstance(size, str) and size.isdigit():
                    size = int(size)
            vartype = VarType(**vartype)
        return cls(name, vartype, size)