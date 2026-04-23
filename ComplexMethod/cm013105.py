def _get_overload(qualified_name: str) -> torch._ops.OpOverload | None:
    """Obtain the torch op from <namespace>::<op_name>[.<overload>]"""
    # TODO(justinchuby): Handle arbitrary custom ops
    namespace, opname_overload = qualified_name.split("::")
    op_name, *maybe_overload = opname_overload.split(".", 1)
    if namespace == "_operator":
        # Builtin functions
        return getattr(operator, op_name)
    if namespace == "math":
        return getattr(math, op_name)
    if namespace == "torchvision":
        if importlib.util.find_spec("torchvision") is None:
            logger.warning("torchvision is not installed. Skipping %s", qualified_name)
            return None
    try:
        op_packet = getattr(getattr(torch.ops, namespace), op_name)
        if maybe_overload:
            overload = maybe_overload[0]
        elif "default" in op_packet._overload_names or "" in op_packet._overload_names:
            # Has a default overload
            overload = "default"
        else:
            logger.warning(
                "'%s' does not have a 'default' overload. This could be an error in specifying the op name. Ignoring.",
                qualified_name,
                stacklevel=1,
            )
            return None

        return getattr(op_packet, overload)  # type: ignore[call-overload]
    except AttributeError:
        if qualified_name.endswith("getitem"):
            # This is a special case where we registered the function incorrectly,
            # but for BC reasons (pt<=2.4) we need to keep it.
            return None
        logger.info("'%s' is not found in this version of PyTorch.", qualified_name)
        return None
    except Exception:
        logger.exception("Failed to find torch op '%s'", qualified_name)
        return None