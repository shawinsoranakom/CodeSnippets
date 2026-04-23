def normalize_attributes(attributes):
    normalized = []
    for name, value in attributes:
        if name == "class" and value:
            # Special case handling of 'class' attribute, so that comparisons
            # of DOM instances are not sensitive to ordering of classes.
            value = " ".join(
                sorted(value for value in ASCII_WHITESPACE.split(value) if value)
            )
        # Boolean attributes without a value is same as attribute with value
        # that equals the attributes name. For example:
        #   <input checked> == <input checked="checked">
        if name in BOOLEAN_ATTRIBUTES:
            if not value or value == name:
                value = None
        elif value is None:
            value = ""
        normalized.append((name, value))
    return normalized