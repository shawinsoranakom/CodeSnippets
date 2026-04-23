def try_ann_to_type(ann, loc, rcb=None):
    ann_args = typing.get_args(ann)  # always returns a tuple!

    if ann is inspect.Signature.empty:
        return TensorType.getInferred()
    if ann is None:
        return NoneType.get()
    if inspect.isclass(ann) and is_tensor(ann):
        return TensorType.get()
    if is_tuple(ann):
        # Special case for the empty Tuple type annotation `Tuple[()]`
        if len(ann_args) == 1 and ann_args[0] == ():
            return TupleType([])
        return TupleType([try_ann_to_type(a, loc) for a in ann_args])
    if is_list(ann):
        elem_type = try_ann_to_type(ann_args[0], loc)
        if elem_type:
            return ListType(elem_type)
    if is_dict(ann):
        key = try_ann_to_type(ann_args[0], loc)
        value = try_ann_to_type(ann_args[1], loc)
        # Raise error if key or value is None
        if key is None:
            raise ValueError(
                f"Unknown type annotation: '{ann_args[0]}' at {loc.highlight()}"
            )
        if value is None:
            raise ValueError(
                f"Unknown type annotation: '{ann_args[1]}' at {loc.highlight()}"
            )
        return DictType(key, value)
    if is_optional(ann):
        if issubclass(ann_args[1], type(None)):
            contained = ann_args[0]
        else:
            contained = ann_args[1]
        valid_type = try_ann_to_type(contained, loc)
        if not valid_type:
            raise AssertionError(
                f"Unsupported annotation {repr(ann)} could not be resolved because "
                f"{repr(contained)} could not be resolved. At\n{repr(loc)}"
            )
        return OptionalType(valid_type)
    if is_union(ann):
        # TODO: this is hack to recognize NumberType
        if set(ann_args) == {int, float, complex}:
            return NumberType.get()
        inner: List = []
        # We need these extra checks because both `None` and invalid
        # values will return `None`
        # TODO: Determine if the other cases need to be fixed as well
        for a in typing.get_args(ann):
            if a is None:
                inner.append(NoneType.get())
            maybe_type = try_ann_to_type(a, loc)
            if not maybe_type:
                raise AssertionError(
                    f"Unsupported annotation {repr(ann)} could not be resolved because "
                    f"{repr(a)} could not be resolved. At\n{repr(loc)}"
                )
            inner.append(maybe_type)
        return UnionType(inner)  # type: ignore[arg-type]
    if torch.distributed.rpc.is_available() and is_rref(ann):
        return RRefType(try_ann_to_type(ann_args[0], loc))
    if is_future(ann):
        return FutureType(try_ann_to_type(ann_args[0], loc))
    if is_await(ann):
        elementType = try_ann_to_type(ann_args[0], loc) if ann_args else AnyType.get()
        return AwaitType(elementType)
    if ann is float:
        return FloatType.get()
    if ann is complex:
        return ComplexType.get()
    if ann is int or ann is torch.SymInt:
        return IntType.get()
    if ann is str:
        return StringType.get()
    if ann is bool:
        return BoolType.get()
    if ann is Any:
        return AnyType.get()
    if ann is type(None):
        return NoneType.get()
    if inspect.isclass(ann) and hasattr(ann, "__torch_script_interface__"):
        return InterfaceType(ann.__torch_script_interface__)
    if ann is torch.device:
        return DeviceObjType.get()
    if ann is torch.Generator:
        return _GeneratorType.get()
    if ann is torch.Stream:
        return StreamObjType.get()
    if ann is torch.dtype:
        return IntType.get()  # dtype not yet bound in as its own type
    if ann is torch.qscheme:
        return IntType.get()  # qscheme not yet bound in as its own type

    if inspect.isclass(ann) and issubclass(ann, enum.Enum):
        if _get_script_class(ann) is None:
            scripted_class = torch.jit._script._recursive_compile_class(ann, loc)
            name = scripted_class.qualified_name()
        else:
            name = _qualified_name(ann)
        return EnumType(name, get_enum_value_type(ann, loc), list(ann))
    if inspect.isclass(ann):
        maybe_script_class = _get_script_class(ann)
        if maybe_script_class is not None:
            return maybe_script_class
        if torch._jit_internal.can_compile_class(ann):
            return torch.jit._script._recursive_compile_class(ann, loc)

    # Maybe resolve a NamedTuple to a Tuple Type
    if rcb is None:
        rcb = _fake_rcb
    # pyrefly: ignore [bad-argument-type]
    return torch._C._resolve_type_from_object(ann, loc, rcb)