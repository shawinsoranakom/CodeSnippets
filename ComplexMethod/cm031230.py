def _tclobj_to_py(val):
    """Return value converted from Tcl object to Python object."""
    if val and hasattr(val, '__len__') and not isinstance(val, str):
        if getattr(val[0], 'typename', None) == 'StateSpec':
            val = _list_from_statespec(val)
        else:
            val = list(map(_convert_stringval, val))

    elif hasattr(val, 'typename'): # some other (single) Tcl object
        val = _convert_stringval(val)

    if isinstance(val, tuple) and len(val) == 0:
        return ''
    return val