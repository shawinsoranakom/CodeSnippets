def extract_shape(*args, allow_cpu_scalar_tensors: bool) -> ShapeType | None:
    shape = None
    scalar_shape = None

    # pyrefly: ignore [bad-assignment]
    for arg in args:
        if isinstance(arg, Number):
            continue
        elif isinstance(arg, TensorLike):
            if allow_cpu_scalar_tensors and is_cpu_scalar_tensor(arg):
                scalar_shape = arg.shape
                continue

            if shape is None:
                shape = arg.shape

            if not is_same_shape(shape, arg.shape):
                return None
        else:
            return None

    return shape if shape is not None else scalar_shape