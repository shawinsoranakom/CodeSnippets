def cast_items(exporter, fmt, itemsize, shape=None):
    """Interpret the raw memory of 'exporter' as a list of items with
       size 'itemsize'. If shape=None, the new structure is assumed to
       be 1-D with n * itemsize = bytelen. If shape is given, the usual
       constraint for contiguous arrays prod(shape) * itemsize = bytelen
       applies. On success, return (items, shape). If the constraints
       cannot be met, return (None, None). If a chunk of bytes is interpreted
       as NaN as a result of float conversion, return ('nan', None)."""
    bytelen = exporter.nbytes
    if shape:
        if prod(shape) * itemsize != bytelen:
            return None, shape
    elif shape == []:
        if exporter.ndim == 0 or itemsize != bytelen:
            return None, shape
    else:
        n, r = divmod(bytelen, itemsize)
        shape = [n]
        if r != 0:
            return None, shape

    mem = exporter.tobytes()
    byteitems = [mem[i:i+itemsize] for i in range(0, len(mem), itemsize)]

    items = []
    for v in byteitems:
        item = struct.unpack(fmt, v)[0]
        if item != item:
            return 'nan', shape
        items.append(item)

    return (items, shape) if shape != [] else (items[0], shape)