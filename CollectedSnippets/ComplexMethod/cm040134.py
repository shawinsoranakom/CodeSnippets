def get(identifier):
    """Retrieves a Keras initializer object via an identifier.

    The `identifier` may be the string name of a initializers function or class
    (case-sensitively).

    >>> identifier = 'Ones'
    >>> keras.initializers.get(identifier)
    <...keras.initializers.initializers.Ones...>

    You can also specify `config` of the initializer to this function by passing
    dict containing `class_name` and `config` as an identifier. Also note that
    the `class_name` must map to a `Initializer` class.

    >>> cfg = {'class_name': 'Ones', 'config': {}}
    >>> keras.initializers.get(cfg)
    <...keras.initializers.initializers.Ones...>

    In the case that the `identifier` is a class, this method will return a new
    instance of the class by its constructor.

    You may also pass a callable function with a signature that includes `shape`
    and `dtype=None` as an identifier.

    >>> fn = lambda shape, dtype=None: ops.ones(shape, dtype)
    >>> keras.initializers.get(fn)
    <function <lambda> at ...>

    Alternatively, you can pass a backend tensor or numpy array as the
    `identifier` to define the initializer values directly. Note that when
    calling the initializer, the specified `shape` argument must be the same as
    the shape of the tensor.

    >>> tensor = ops.ones(shape=(5, 5))
    >>> keras.initializers.get(tensor)
    <function get.<locals>.initialize_fn at ...>

    Args:
        identifier: A string, dict, callable function, or tensor specifying
            the initializer. If a string, it should be the name of an
            initializer. If a dict, it should contain the configuration of an
            initializer. Callable functions or predefined tensors are also
            accepted.

    Returns:
        Initializer instance base on the input identifier.
    """
    if identifier is None:
        return None
    if isinstance(identifier, dict):
        obj = deserialize(identifier)
    elif isinstance(identifier, str):
        config = {"class_name": str(identifier), "config": {}}
        obj = deserialize(config)
    elif ops.is_tensor(identifier) or isinstance(
        identifier, (np.generic, np.ndarray)
    ):

        def initialize_fn(shape, dtype=None):
            dtype = backend.standardize_dtype(dtype)
            if backend.standardize_shape(shape) != backend.standardize_shape(
                identifier.shape
            ):
                raise ValueError(
                    f"Expected `shape` to be {identifier.shape} for direct "
                    f"tensor as initializer. Received shape={shape}"
                )
            return ops.cast(identifier, dtype)

        obj = initialize_fn
    else:
        obj = identifier

    if callable(obj):
        if inspect.isclass(obj):
            obj = obj()
        return obj
    else:
        raise ValueError(
            f"Could not interpret initializer identifier: {identifier}"
        )