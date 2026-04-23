def handle_traced_output(
    example_value: Any,
    tx: "InstructionTranslatorBase",
    proxy: torch.fx.Proxy,
    options: dict[str, Any],
    subclass_type: type | None,
    target_cls: type[VTTypeAlias],
) -> VariableTracker:
    import torch._functorch.vmap
    import torch._subclasses.fake_tensor
    import torch._utils

    if isinstance(example_value, torch.Tensor):
        # Check if the result is a sparse tensor -
        # We generally don't support sparse tensor so better to graph break here
        if is_sparse_any(example_value) and (
            not tx.export or not config.capture_sparse_compute
        ):
            unimplemented(
                gb_type="Attempted to wrap sparse Tensor with VariableTracker",
                context=str(example_value),
                explanation="torch.compile does not support sparse Tensors with VariableTracker",
                hints=[*graph_break_hints.SPARSE_TENSOR],
            )
        var = construct_tensor_variable(
            target_cls, tx, proxy, example_value, subclass_type, options
        )
        # NOTE: [Side effect tracking for newly constructed tensor]
        # For newly constructed objects that have mutable attributes, we usually
        # construct their VariableTracker via `track_object_new`, but since
        # tensor variable construction is a bit different, we handle them
        # specially here. This ensures that codegen will actually generate the
        # attribute mutations on this tensor.
        #
        # NOTE we pass a dummy object as the `item` argument to avoid
        # constructing a dummy _tensor_ object. The object isn't used for
        # newly constructed VTs anyways.
        assert isinstance(var, VariableTracker)
        tx.output.side_effects._track_obj(
            proxy, var, mutation_type_cls=AttributeMutationNew
        )
        return var
    elif (
        hasattr(proxy.node.target, "__name__")
        and proxy.node.target.__name__ == "set_state"
        # type: ignore[attr-defined]
        and isinstance(proxy.node.target.__self__, torch._C.Generator)
        or proxy.node.target is torch.random.set_rng_state
    ):
        assert type(proxy.node.target) is not str
        # pyrefly: ignore[bad-argument-type]
        return TorchInGraphFunctionVariable(proxy.node.target)
    elif (
        proxy.node.target is torch._C._DisableFuncTorch
        or proxy.node.target is torch.cuda._is_in_bad_fork
    ):
        return UserDefinedObjectVariable(example_value)
    elif istype(example_value, torch.Size) and all(
        isinstance(x, int) for x in example_value
    ):
        sizes = [ConstantVariable.create(x) for x in example_value]
        return SizeVariable(sizes, **options)
    elif isinstance(example_value, (tuple, list)):
        set_example_value(proxy.node, example_value)
        unpacked = []
        for i, val in enumerate(example_value):
            if val is None:
                # nn.MultiheadAttention() can return None, see issue #175
                unpacked.append(
                    ConstantVariable.create(None, **options),
                )
            else:
                proxy_i = proxy.tracer.create_proxy(
                    kind="call_function",
                    target=operator.getitem,
                    args=(proxy, i),
                    kwargs={},
                )

                if "source" in options:
                    # This path should only trigger for list stealing, so it's
                    # safe to use `GetItemSource`.
                    assert isinstance(example_value, list)
                    source = options["source"]
                    options_i = options.copy()
                    options_i["source"] = GetItemSource(
                        base=source,
                        index=i,
                        index_is_slice=False,
                    )
                else:
                    # use the same options object as parent
                    options_i = options

                # WARNING: this assumes the same target_cls as this tuple/list call
                unpacked.append(
                    # pyrefly: ignore [bad-argument-type]
                    wrap_fx_proxy_cls(
                        # pyrefly: ignore[bad-argument-type]
                        target_cls=target_cls,
                        tx=tx,
                        proxy=proxy_i,
                        example_value=val,
                        **options_i,
                    )
                )
        if isinstance(example_value, torch.Size):
            # NB: Keep the old proxy around.  See SizeVariable for an
            # explanation why
            return SizeVariable(unpacked, proxy, **options)
        elif istype(example_value, tuple):
            return TupleVariable(unpacked, **options)
        elif istype(example_value, (list, immutable_list)):
            return ListVariable(unpacked, **options)
        else:
            assert is_namedtuple(example_value), (
                f"expected namedtuple or structseq but got {type(example_value)}"
            )
            tuple_vt = TupleVariable(
                unpacked,
                mutation_type=options.get("mutation_type", ValueMutationNew()),
            )
            return UserDefinedTupleVariable.get_vt_cls(type(example_value))(
                example_value,
                tuple_vt=tuple_vt,
                **options,  # type: ignore[arg-type]
            )
    elif example_value is None or proxy.node.target is torch.manual_seed:
        return ConstantVariable.create(None, **options)
    elif isinstance(example_value, (torch.SymInt, torch.SymFloat, torch.SymBool)):
        tx.output.current_tracer.track_produced_symints(example_value, proxy)
        set_example_value(proxy.node, example_value)
        return SymNodeVariable.create(tx, proxy, example_value, **options)
    elif (
        isinstance(example_value, torch.Stream)
        and proxy.node.target is get_external_object_by_index
    ) or proxy.node.target in [
        device_interface.current_stream
        for _, device_interface in get_registered_device_interfaces()
    ]:
        set_example_value(proxy.node, example_value)
        index = None
        if proxy.node.target is get_external_object_by_index:
            index = proxy.node.args[0]
        # type: ignore[arg-type]
        return StreamVariable(proxy, example_value, index, **options)
    elif (
        isinstance(example_value, torch.Event)
        and proxy.node.target is get_external_object_by_index
    ) or proxy.node.target in [
        device_interface.current_stream
        for _, device_interface in get_registered_device_interfaces()
    ]:
        index = None
        if proxy.node.target is get_external_object_by_index:
            index = proxy.node.args[0]
        set_example_value(proxy.node, example_value)
        # type: ignore[arg-type]
        return EventVariable(proxy, example_value, index, **options)
    elif (
        inspect.isclass(proxy.node.target)
        and issubclass(proxy.node.target, torch.Event)
    ) or proxy.node.target in [
        device_interface.Event
        for _, device_interface in get_registered_device_interfaces()
    ]:
        set_example_value(proxy.node, example_value)
        return EventVariable(proxy, example_value, None, **options)
    elif proxy.node.target == "query" and proxy.node.op == "call_method":
        set_example_value(proxy.node, example_value)
        return ConstantVariable(example_value, **options)
    elif (
        example_value is not None
        and isinstance(example_value, torch.Event)
        and proxy.node.target == "record_event"
        and proxy.node.op == "call_method"
    ):
        set_example_value(proxy.node, example_value)
        return EventVariable(proxy, example_value, None, **options)
    elif isinstance(example_value, int) and (
        proxy.node.target
        in [
            torch.sym_int,
            torch.sym_max,
            torch.sym_min,
            getattr,
            operator.getitem,
            torch._utils._element_size,
            torch.seed,
            operator.mod,
            torch._functorch.vmap._validate_and_get_batch_size,
            torch._functorch.predispatch._vmap_increment_nesting,
            torch._functorch.predispatch._vmap_decrement_nesting,
            # some mac builds are missing torch.distributed.get_rank()
            getattr(torch.distributed, "get_rank", _missing),
            getattr(torch.distributed, "get_world_size", _missing),
            # This always wants to be in the graph, even if the constraint
            # results in a constant int
            torch._constrain_as_size,
        ]
        or (
            # TODO: this is a little sus, because we didn't check what the self is
            proxy.node.op == "call_method" and proxy.node.target == "bit_length"
        )
    ):
        set_example_value(proxy.node, example_value)
        return ConstantVariable.create(example_value, **options)
    elif isinstance(example_value, torch.backends.cuda.SDPAParams):
        from .sdpa import SDPAParamsVariable

        set_example_value(proxy.node, example_value)
        return SDPAParamsVariable(proxy, **options)
    elif isinstance(example_value, bool) and (
        proxy.node.target
        in [
            torch._C._are_functorch_transforms_active,
            torch._C._functorch.is_batchedtensor,
            torch.backends.cuda.is_flash_attention_available,
            torch.backends.cuda.can_use_flash_attention,
            torch.backends.cuda.can_use_efficient_attention,
            torch._C._get_cudnn_sdp_enabled,
            torch._C._get_flash_sdp_enabled,
            torch._C._get_mem_efficient_sdp_enabled,
            torch._C._get_math_sdp_enabled,
            torch._C._get_overrideable_sdp_enabled,
            torch._C._is_autocast_available,
            "is_integer",
        ]
        + list(supported_const_comparison_op_values.keys())
    ):
        set_example_value(proxy.node, example_value)
        return ConstantVariable.create(example_value, **options)
    elif isinstance(example_value, (int, float, bool)) and (
        proxy.node.target is call_torchbind
        or proxy.node.target is flat_apply
        or (proxy.node.op == "call_method" and proxy.node.target == "item")
    ):
        set_example_value(proxy.node, example_value)
        return ConstantVariable.create(example_value, **options)
    elif isinstance(example_value, float) or proxy.node.target in ["hex", "__round__"]:
        set_example_value(proxy.node, example_value)
        return ConstantVariable.create(example_value, **options)
    elif isinstance(example_value, torch._library.fake_class_registry.FakeScriptObject):
        # example_value is already a FakeScriptObject (e.g. returned by getitem
        # on a container whose fake kernel returns a FakeScriptObject).  No need
        # to convert it — just wrap the proxy directly.
        return TorchScriptObjectVariable.create(
            proxy,
            example_value,
        )
    elif is_opaque_type(type(example_value)):
        # This is for handling opaque objects in custom ops
        if is_opaque_value_type(type(example_value)):
            return TorchScriptObjectVariable.create(
                example_value,  # pyrefly: ignore[bad-argument-type]
                example_value,
            )
        fake_script_obj = torch._library.fake_class_registry.maybe_to_fake_obj(
            tx.output.fake_mode, example_value
        )
        return TorchScriptObjectVariable.create(
            proxy,
            fake_script_obj,
        )
    else:
        unimplemented(
            gb_type="torch.* op returned non-Tensor",
            context=f"example_value type: {typestr(example_value)}; op: {proxy.node.op}; target: {proxy.node.target}",
            explanation="torch.* ops that return a non-Tensor cannot be traced into the Dynamo FX graph output",
            hints=[],
        )