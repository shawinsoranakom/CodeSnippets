def register_opaque_type(
    cls: Any,
    *,
    typ: str,
    hoist=False,
    guard_fn: Any = None,
    members: dict[str, MemberType] | None = None,
    reconstruct_fn: ReconstructFn | None = None,
) -> None:
    """
    Registers the given type as an opaque type which allows this to be consumed
    by a custom operator.

    The type name will be automatically generated from the class's fully
    qualified name (ex. my_module.MyClass).

    Args:
        cls (type): The class to register as an opaque type.
        typ (str): Either "reference" or "value". See Note [Opaque Objects] for
            more details.
        hoist (bool): Only applies to value types. A hoist=True value type
            object is lifted as an input to the torch.compile'd graph, instead
            of being a constant baked into the graph. This is useful to
            improve compilation times in hierarchical compilation
            (e.g., change your custom ops to use hoisted strings to avoid
            baking the string into the Dynamo/AOTAutograd/FX graphs).
            This flag does nothing for reference types.
        guard_fn (callable | None): A function that takes an instance of the opaque
            object and returns a list of values to guard on. These values will be compared
            for equality on each function call, triggering recompilation if they change.
            Only applicable for reference types.
            Example: lambda obj: [obj.x, obj.y]
        members (dict[str, MemberType] | None): Dictionary mapping member names
            (attributes, properties, or methods) to their MemberType, which controls
            how they are handled during torch.compile tracing:
            - MemberType.USE_REAL: Evaluates with the real object at compile time and
              bakes the result as a constant
            - MemberType.INLINED: Inlines the method call into the trace
    """
    import torch.utils._pytree as pytree

    # Prevent registration of built-in types (int, str, list, dict, etc.) and torch.Tensor
    if cls.__module__ == "builtins" or cls is torch.Tensor:
        raise ValueError(
            f"Unable to register built-in type {cls} as an opaque type. "
            "Please wrap it in a custom class and register the custom class as opaque."
        )

    if cls in pytree.SUPPORTED_NODES:
        raise ValueError(
            f"{cls} cannot be registered as an opaque object as it has been "
            "registered as a pytree. Opaque objects must be pytree leaves."
        )

    # Value types store the real object directly during tracing (no
    # FakeScriptObject wrapper), so they don't need OpaqueBaseMeta.
    if typ != "value" and not isinstance(cls, OpaqueBaseMeta):
        raise TypeError(
            f"Opaque type {cls} must subclass torch._opaque_base.OpaqueBase "
            "or 'metaclass=torch._opaque_base.OpaqueBaseMeta'. "
            "This is required so that FakeScriptObject can be registered "
            "as a virtual subclass, allowing isinstance() checks to work "
            "during torch.compile tracing. "
        )

    if typ not in ["reference", "value"]:
        raise AssertionError(
            f"Opaque type must be either 'reference' or 'value', got {typ!r}"
        )

    if typ == "value":
        # Enums use identity-based equality (singletons), which is fine for guarding.
        if not issubclass(cls, Enum) and cls.__eq__ is object.__eq__:  # type: ignore[comparison-overlap]
            raise TypeError(
                f"Value-type opaque object of type {cls} is "
                "expected to have a non-default `__eq__` "
                "implementation as we will use this in torch.compile "
                "to guard on the equality of objects."
            )

        # Class with a custom `__eq__` without `__hash__` won't inherit the default
        # `__hash__` from object; see https://stackoverflow.com/a/1608907.
        if cls.__hash__ is None:  # type: ignore[comparison-overlap]
            raise TypeError(
                f"Value-type opaque object of type {cls} is "
                "expected to have a non-default `__hash__` "
                "implementation as we will use this in torch.compile "
                "for FakeTensor caching."
            )

        # Enums are special-cased in get_opaque_obj_repr.
        if not issubclass(cls, Enum) and not hasattr(cls, "__fx_repr__"):
            raise TypeError(
                f"Value-type opaque object of type {cls} is "
                "expected to have a `__fx_repr__` method "
                "implementation as we will use this to reconstruct "
                "the object in the FX codegen. __fx_repr__ should return "
                "a tuple of (repr_string, dict[str, type])."
            )

        if guard_fn is not None:
            raise TypeError(
                "No need to specify `guard_fn` for "
                f"value-type opaque class {cls} as it will be guarded based "
                "on `__eq__`."
            )

    # Generate a fully qualified name by combining module and qualname
    name = f"{cls.__module__}.{cls.__qualname__}"

    type_info = _OpaqueTypeInfo(
        name, typ, guard_fn, members or {}, hoist, reconstruct_fn
    )
    _OPAQUE_TYPES[cls] = type_info
    _OPAQUE_TYPES_BY_NAME[name] = type_info

    torch._C._register_opaque_type(name)