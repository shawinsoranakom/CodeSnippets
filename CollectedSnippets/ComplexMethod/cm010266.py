def _make_argument_spec(node, token_names) -> ArgumentSpec:
    from torch import ScriptObject, SymBool, SymFloat, SymInt
    from torch._library.fake_class_registry import FakeScriptObject

    if isinstance(node, (int, bool, float, type(None), str)):
        # For const outputs we just directly return this
        return ConstantArgument(name="", value=node)

    if "val" not in node.meta:
        raise AssertionError(
            f"{node} is not a constant or a node with a 'val' metadata field"
        )
    val = node.meta["val"]
    if node.name in token_names:
        return TokenArgument(name=node.name)
    elif is_fake(val):
        return TensorArgument(name=node.name)
    elif isinstance(val, SymInt):
        return SymIntArgument(name=node.name)
    elif isinstance(val, SymFloat):
        return SymFloatArgument(name=node.name)
    elif isinstance(val, SymBool):
        return SymBoolArgument(name=node.name)
    elif isinstance(val, ScriptObject):
        return CustomObjArgument(name=node.name, class_fqn=val._type().qualified_name())  # type: ignore[attr-defined]
    elif isinstance(val, FakeScriptObject):
        return CustomObjArgument(
            name=node.name, class_fqn=val.script_class_name, fake_val=val
        )
    elif is_opaque_type(type(val)):
        return CustomObjArgument(
            name=node.name, class_fqn=get_opaque_type_name(type(val)), fake_val=val
        )
    elif isinstance(val, (int, bool, str, float, type(None))):
        return ConstantArgument(name=node.name, value=val)
    else:
        raise AssertionError(
            f"Encountered an unsupported object of type {type(val)} "
            f"while writing the metadata for exported program"
        )