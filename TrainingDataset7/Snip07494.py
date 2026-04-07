def pretty_name(obj):
    return obj.__name__ if obj.__class__ == type else obj.__class__.__name__