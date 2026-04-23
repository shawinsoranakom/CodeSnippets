def create_with_source(cls, value: Any, source: Source) -> "BaseTorchVariable":
        if inspect.isclass(value):
            install_guard(source.make_guard(GuardBuilder.CLASS_MATCH))
        elif inspect.ismodule(value):
            install_guard(source.make_guard(GuardBuilder.MODULE_MATCH))
        elif inspect.isfunction(value):
            install_guard(source.make_guard(GuardBuilder.CLOSURE_MATCH))
        elif inspect.isbuiltin(value) or isinstance(
            value, (torch._ops.OpOverload, torch._ops.OpOverloadPacket)
        ):
            install_guard(source.make_guard(GuardBuilder.BUILTIN_MATCH))
        elif is_wrapper_or_member_descriptor(value) or isinstance(
            value, torch._dynamo.compiled_autograd.Op
        ):
            # Dont need to guard on wrappers
            pass
        else:
            install_guard(source.make_guard(GuardBuilder.FUNCTION_MATCH))
        return cls(value, source=source)