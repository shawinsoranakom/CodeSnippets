def _wrap_fx_preexisting_tensor(
    target_cls: type[VTTypeAlias],
    tx: "InstructionTranslatorBase",
    proxy: torch.fx.Proxy,
    tensor: torch.Tensor,
    subclass_type: type | None = None,
    **options: Any,
) -> VTTypeAlias:
    from ..symbolic_convert import InstructionTranslatorBase

    assert isinstance(tensor, torch.Tensor), (
        f"_wrap_fx_preexisting_tensor expected tensor, got {type(tensor)}"
    )

    assert isinstance(tx, InstructionTranslatorBase)
    if "guards" in options and options["guards"] is not None:
        tx.output.guards.update(options["guards"])

    # Placeholders always carry example_value in node.meta.
    # non-placeholders always have no example_value in node.meta
    if proxy.node.op == "placeholder":
        assert "example_value" in proxy.node.meta, (
            f"placeholder {proxy} doesn't have 'example_value' in node.meta"
        )
    else:
        assert "example_value" not in proxy.node.meta, (
            f"{proxy.node.meta['example_value']}"
        )

    # See NOTE: [Deferring tensor pack/unpack hooks until runtime]
    with torch._dynamo.utils._disable_saved_tensors_hooks_during_tracing():
        # Handle recursive calls here
        if maybe_get_fake_mode(tensor) is tx.fake_mode:
            pass
        else:
            cache_real_value_when_export(tx, proxy, tensor)
            if tx.export:
                # The legacy behavior for real value cache with subclasses was
                # to perform a clone WITHOUT preserving the subclass.  It's
                # not entirely clear this is what you actually want though.
                with torch._C.DisableTorchFunctionSubclass():
                    # type: ignore[attr-defined]
                    proxy.tracer.real_value_cache[proxy.node] = _clone_input(
                        tensor, tx.fake_mode
                    )
            # NB: If we're ignoring subclass, then the expectation is you will
            # take the returned TensorVariable and wrap it into a more
            # accurate TensorVariable that is able to track subclass-ness;
            # otherwise this is wrong!
            kwargs = {
                "is_tensor": target_cls
                in (TensorVariable, TensorWithTFOverrideVariable),
            }
            assert "source" in options and options["source"] is not None
            kwargs["source"] = options["source"]
            # pyrefly: ignore [missing-argument]
            tensor = wrap_to_fake_tensor_and_record(tensor, tx=tx, **kwargs)

        if tensor.device.type != "meta" and (
            maybe_get_fake_mode(tensor) is not tx.fake_mode
        ):
            raise InternalTorchDynamoError(
                "`tensor` needs to be a `FakeTensor`"
                f"wrapped by this instance of Dynamo. Found: {tensor}"
            )

    return construct_tensor_variable(
        target_cls, tx, proxy, tensor, subclass_type, options
    )