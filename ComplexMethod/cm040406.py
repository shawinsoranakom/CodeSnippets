def moveaxis(x, source, destination):
    x = convert_to_tensor(x)

    _source = to_tuple_or_list(source)
    _destination = to_tuple_or_list(destination)
    _source = tuple(canonicalize_axis(i, x.ndim) for i in _source)
    _destination = tuple(canonicalize_axis(i, x.ndim) for i in _destination)
    if len(_source) != len(_destination):
        raise ValueError(
            "Inconsistent number of `source` and `destination`. "
            f"Received: source={source}, destination={destination}"
        )
    # Directly return x if no movement is required
    if _source == _destination:
        return x
    perm = [i for i in range(x.ndim) if i not in _source]
    for dest, src in sorted(zip(_destination, _source)):
        perm.insert(dest, src)
    return tf.transpose(x, perm)