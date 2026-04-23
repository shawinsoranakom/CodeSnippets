def moveaxis(x, source, destination):
    x = get_ov_output(x)
    if isinstance(source, int):
        source = [source]
    if isinstance(destination, int):
        destination = [destination]

    ndim = x.get_partial_shape().rank.get_length()
    source = [axis if axis >= 0 else axis + ndim for axis in source]
    destination = [axis if axis >= 0 else axis + ndim for axis in destination]

    axes = list(range(ndim))
    for src, dst in zip(source, destination):
        axes.remove(src)
        axes.insert(dst, src)

    axes_const = ov_opset.constant(axes, Type.i32).output(0)
    return OpenVINOKerasTensor(ov_opset.transpose(x, axes_const).output(0))