def get_base_classes(cls):
    """Get the base classes of a class.

    These are used to determine the output of the nodes.
    """
    if hasattr(cls, "__bases__") and cls.__bases__:
        bases = cls.__bases__
        result = []
        for base in bases:
            if any(_type in base.__module__ for _type in ["pydantic", "abc"]):
                continue
            result.append(base.__name__)
            base_classes = get_base_classes(base)
            # check if the base_classes are in the result
            # if not, add them
            for base_class in base_classes:
                if base_class not in result:
                    result.append(base_class)
    else:
        result = [cls.__name__]
    if not result:
        result = [cls.__name__]
    return list({*result, cls.__name__})