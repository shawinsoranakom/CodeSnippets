def create_fx_graph_from_captured_output(
    out: CaptureOutput, mod: Any, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> torch.fx.GraphModule:
    assert out.backend_input is not None
    backend_input = out.backend_input

    _, root = torch._dynamo.convert_frame.get_traced_fn(mod)

    flat_real_args = pytree.tree_leaves((args, kwargs))
    torch._dynamo.eval_frame.check_user_input_output(
        flat_real_args, UserErrorType.INVALID_INPUT
    )
    f_globals = out.graph_capture_output.f_globals

    graph_module = backend_input.graph_module
    if isinstance(root, torch.nn.Module):
        graph_module._parameters = root._parameters
        graph_module._buffers = root._buffers
        assert all(not hasattr(graph_module, m) for m in root._modules)
        graph_module._modules.update(root._modules)
        graph_module._non_persistent_buffers_set = root._non_persistent_buffers_set
        if sys.version_info >= (3, 14):
            import annotationlib  # added in 3.14

            annotations = annotationlib.get_annotations(torch.nn.Module)
        else:
            annotations = getattr(torch.nn.Module, "__annotations__", None)
        for name, value in root.__dict__.items():
            if annotations and name not in annotations:
                graph_module.__dict__[name] = value
        graph_module._forward_hooks = root._forward_hooks.copy()
        graph_module._forward_pre_hooks = root._forward_pre_hooks.copy()
        graph_module._backward_hooks = root._backward_hooks.copy()
        graph_module._backward_pre_hooks = root._backward_pre_hooks.copy()
        if graph_module._forward_hooks or graph_module._forward_pre_hooks:
            # Even forward hooks are traced through, they still capture a bunch
            # of state through closure. We need to make sure these data are
            # accessible through the captured module (but the hooks should be
            # disabled).
            assert getattr(graph_module, "_wrapped_call", None) is not None
            assert isinstance(
                graph_module._wrapped_call, torch.fx.graph_module._WrappedCall
            )
            assert graph_module._wrapped_call.cls_call is None

            def dynamo_wrapped_call(self, *args: object, **kwargs: object) -> object:
                assert "forward" not in self.__dict__

                fwd_hooks = self._forward_hooks
                fwd_pre_hooks = self._forward_pre_hooks
                original_forward = type(self).forward

                def patched_forward(self, *args: object, **kwargs: object) -> object:
                    self._forward_hooks = fwd_hooks
                    self._forward_pre_hooks = fwd_pre_hooks
                    return original_forward(self, *args, **kwargs)

                try:
                    self.forward = types.MethodType(patched_forward, self)
                    # pyrefly: ignore [implicit-any]
                    self._forward_hooks = {}
                    # pyrefly: ignore [implicit-any]
                    self._forward_pre_hooks = {}
                    # pyrefly: ignore [invalid-argument]
                    return super(type(self), self).__call__(*args, **kwargs)
                finally:
                    self.__dict__.pop("forward")
                    self._forward_hooks = fwd_hooks
                    self._forward_pre_hooks = fwd_pre_hooks

            # pyrefly: ignore [bad-assignment]
            graph_module._wrapped_call.cls_call = dynamo_wrapped_call

    root = graph_module if isinstance(root, torch.nn.Module) else root
    input_processor = InputProcessor(root, len(args), list(kwargs.keys()))
    dynamo_bytecode_flatten = DynamoBytecodeFlatten(input_processor, out, f_globals)
    dynamo_bytecode_unflatten = DynamoBytecodeUnflatten(input_processor, out, f_globals)

    graph_module.graph._codegen = _DynamoBytecodeCodeGen(
        argument_names(inspect.signature(mod), args, kwargs),
        dynamo_bytecode_flatten,
        dynamo_bytecode_unflatten,
    )  # type: ignore[attr-defined]
    normalize_graph_module(graph_module)
    assert not hasattr(graph_module, "_dynamo_bytecode_flatten")
    assert not hasattr(graph_module, "_dynamo_bytecode_unflatten")
    # pyrefly: ignore [bad-argument-type]
    graph_module._dynamo_bytecode_flatten = dynamo_bytecode_flatten
    # pyrefly: ignore [bad-argument-type]
    graph_module._dynamo_bytecode_unflatten = dynamo_bytecode_unflatten
    delattr(graph_module, "_param_name_to_source")
    graph_module.recompile()
    graph_module.meta["module_call_specs"] = (
        out.graph_capture_output.output_graph.export_metadata.module_call_spec
    )
    assert out.backend_input is not None
    graph_module.meta["fake_mode"] = out.backend_input.fake_mode  # type: ignore[attr-defined]
    graph_module.meta["fake_mode"].allow_non_fake_inputs = True
    tracing_context = TracingContext(graph_module.meta["fake_mode"])
    tracing_context.tensor_to_context = out.backend_input.tensor_to_context  # type: ignore[attr-defined]
    graph_module.meta["tracing_context"] = tracing_context
    return graph_module