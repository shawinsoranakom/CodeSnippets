def _get_repr(arg: object) -> str:
            if isinstance(arg, Node):  # first because common
                return repr(arg)
            elif isinstance(arg, tuple) and hasattr(arg, "_fields"):
                # Handle NamedTuples (if it has `_fields`) via add_global.
                qualified_name = _get_qualified_name(type(arg))
                global_name = add_global(qualified_name, type(arg))
                return f"{global_name}{repr(tuple(arg))}"
            elif isinstance(
                arg, (torch._ops.OpOverload, torch._ops.HigherOrderOperator)
            ):
                qualified_name = _get_qualified_name(arg)
                global_name = add_global(qualified_name, arg)
                return f"{global_name}"
            elif isinstance(arg, enum.Enum):
                cls = arg.__class__
                clsname = add_global(cls.__name__, cls)
                return f"{clsname}.{arg.name}"
            elif isinstance(arg, torch.Tensor):
                size = list(arg.size())
                dtype = str(arg.dtype).split(".")[-1]
                return f"torch.Tensor(size={size}, dtype={dtype})"
            elif isinstance(arg, tuple):
                if len(arg) == 1:
                    return f"({_get_repr(arg[0])},)"
                else:
                    return "(" + ", ".join(_get_repr(a) for a in arg) + ")"
            elif isinstance(arg, list):
                return "[" + ", ".join(_get_repr(a) for a in arg) + "]"
            elif isinstance(arg, slice):
                return f"slice({_get_repr(arg.start)}, {_get_repr(arg.stop)}, {_get_repr(arg.step)})"
            elif is_opaque_value_type(type(arg)):
                obj_repr, opaque_types = get_opaque_obj_repr(arg)
                for n, t in opaque_types.items():
                    add_global(n, t)
                return obj_repr
            else:
                return blue(repr(arg))