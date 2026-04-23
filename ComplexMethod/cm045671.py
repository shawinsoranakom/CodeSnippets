def wrap(input_type) -> DType:
    assert input_type != Optional
    assert input_type != Tuple
    assert input_type != Callable
    assert input_type != Array
    assert input_type != List
    assert input_type != Json
    assert input_type != PyObjectWrapper
    assert input_type != ...

    from pathway.internals.schema import ColumnSchema

    if isinstance(input_type, ColumnSchema):
        return input_type.dtype

    if isinstance(input_type, DType):
        return input_type
    if typing.get_origin(input_type) == np.dtype:
        (input_type,) = typing.get_args(input_type)
    if input_type in (NoneType, None):
        return NONE
    elif input_type == typing.Any:
        return ANY
    elif input_type == api.Pointer:
        return ANY_POINTER
    elif typing.get_origin(input_type) == api.Pointer:
        args = typing.get_args(input_type)
        return Pointer(*args)
    elif isinstance(input_type, str):
        return ANY  # TODO: input_type is annotation for class
    elif typing.get_origin(input_type) == collections.abc.Callable:
        c_args = get_args(input_type)
        if c_args == ():
            return Callable(..., ANY)
        arg_types, ret_type = c_args
        if isinstance(arg_types, Tuple):
            callable_args: tuple[DType, ...] | EllipsisType = arg_types.args
        else:
            assert isinstance(arg_types, EllipsisType)
            callable_args = arg_types
        assert isinstance(ret_type, DType), type(ret_type)
        return Callable(callable_args, ret_type)
    elif (
        typing.get_origin(input_type) in (typing.Union, UnionType)
        and len(typing.get_args(input_type)) == 2
        and isinstance(None, typing.get_args(input_type)[1])
    ):
        arg, _ = get_args(input_type)
        assert isinstance(arg, DType)
        return Optional(arg)
    elif input_type in [list, tuple, typing.List, typing.Tuple]:
        return ANY_TUPLE
    elif (
        input_type == js.Json
        or input_type == dict
        or typing.get_origin(input_type) == dict
    ):
        return JSON
    elif typing.get_origin(input_type) == list:
        args = get_args(input_type)
        (arg,) = args
        return List(wrap(arg))
    elif typing.get_origin(input_type) == tuple:
        args = get_args(input_type)
        if args[-1] == ...:
            arg, _ = args
            return List(wrap(arg))
        else:
            return Tuple(*[wrap(arg) for arg in args])
    elif input_type == np.ndarray:
        return ANY_ARRAY
    elif typing.get_origin(input_type) == np.ndarray:
        dims, wrapped = typing.get_args(input_type)
        if dims == typing.Any:
            return Array(n_dim=None, wrapped=wrap(wrapped))
        return Array(n_dim=len(typing.get_args(dims)), wrapped=wrap(wrapped))
    elif input_type == api.PyObjectWrapper:
        return ANY_PY_OBJECT_WRAPPER
    elif typing.get_origin(input_type) == api.PyObjectWrapper:
        (inner,) = typing.get_args(input_type)
        return PyObjectWrapper(inner)
    elif isinstance(input_type, type) and issubclass(input_type, Enum):
        return ANY
    elif input_type == datetime.datetime:
        raise TypeError(
            f"Unsupported type {input_type}, use pw.DATE_TIME_UTC or pw.DATE_TIME_NAIVE"
        )
    elif input_type == datetime.timedelta:
        raise TypeError(f"Unsupported type {input_type}, use pw.DURATION")
    elif typing.get_origin(input_type) == asyncio.Future:
        args = get_args(input_type)
        (arg,) = args
        return Future(wrap(arg))
    else:
        dtype = {
            int: INT,
            bool: BOOL,
            str: STR,
            float: FLOAT,
            datetime_types.Duration: DURATION,
            datetime_types.DateTimeNaive: DATE_TIME_NAIVE,
            datetime_types.DateTimeUtc: DATE_TIME_UTC,
            np.int32: INT,
            np.int64: INT,
            np.float32: FLOAT,
            np.float64: FLOAT,
            bytes: BYTES,
        }.get(input_type, None)
        if dtype is None:
            raise TypeError(f"Unsupported type {input_type!r}.")
        return dtype