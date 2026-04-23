def _js_eq(a, b):
    # NaN != any
    if _NaN in (a, b):
        return False
    # Object is Object
    if isinstance(a, type(b)) and isinstance(b, (dict, list)):
        return operator.is_(a, b)
    # general case
    if a == b:
        return True
    # null == undefined
    a_b = set((a, b))
    if a_b & _nullish:
        return a_b <= _nullish
    a, b = _js_to_primitive(a), _js_to_primitive(b)
    if not isinstance(a, compat_basestring):
        a, b = b, a
    # Number to String: convert the string to a number
    # Conversion failure results in ... false
    if isinstance(a, compat_basestring):
        return float_or_none(a) == b
    return a == b