def member_dir(member):
    if member.__class__._member_type_ is object:
        allowed = set(['__class__', '__doc__', '__eq__', '__hash__', '__module__', 'name', 'value'])
    else:
        allowed = set(dir(member))
    for cls in member.__class__.mro():
        for name, obj in cls.__dict__.items():
            if name[0] == '_':
                continue
            if isinstance(obj, enum.property):
                if obj.fget is not None or name not in member._member_map_:
                    allowed.add(name)
                else:
                    allowed.discard(name)
            elif name not in member._member_map_:
                allowed.add(name)
    return sorted(allowed)