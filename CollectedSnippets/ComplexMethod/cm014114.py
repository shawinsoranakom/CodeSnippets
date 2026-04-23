def _wrap_to_fake_tensor_and_record_impl(
    e: Any,
    tx: "InstructionTranslatorBase",
    *,
    source: Source | None,
    is_tensor: bool,
    parent_context: Any | None = None,
) -> Any:
    if (
        type(e) in (torch.Tensor, torch.nn.Parameter, FakeTensor)
        or isinstance(e, torch.Tensor)
        or is_traceable_wrapper_subclass(e)
    ):
        assert source is not None
        static_shapes, _reason = tensor_always_has_static_shape(
            e,
            is_tensor,
            tensor_source=source,
        )

        if not parent_context:
            symbolic_context = _automatic_dynamic(e, tx, source, static_shapes)
        else:
            # Parent contexts are passed in when we are recursively creating
            # fake tensors for subclasses. A better design would be not to create a
            # parent/child relationship, but to recursively call _automatic_dynamic
            # as we recursively call wrap_to_fake_tensor_and_record. This runs
            # into bugs around how meta_utils knows and works to create fake tensors
            # with tensor subclasses. Ideally, dynamo would drive both the recursive
            # wrap_to_fake_tensor_and_record and _automatic_dynamic policy creation.
            assert isinstance(source, AttrSource)
            inner_context_name = source.member
            symbolic_context = parent_context.inner_contexts[inner_context_name]

        log.debug(
            "wrap_to_fake %s %s %s %s",
            source.name,
            tuple(e.shape),
            symbolic_context,
            type(e),
        )

        # Note [enable_python_dispatcher in dynamo]
        # Dynamo disables itself when it runs fake tensor prop, which means that tensor subclasses
        # have no way to know (purely based off of global state) if they are currently being run under compile or not.
        # we use enable_python_dispatcher mainly to tweak the DispatchKeyState so that subclass authors
        # can check it to know if they are running in an eager context or not
        with enable_python_dispatcher():
            assert tx.fake_mode is not None
            fake_e = wrap_fake_exception(
                lambda: tx.fake_mode.from_tensor(
                    e,  # type: ignore[arg-type]
                    source=source,
                    symbolic_context=symbolic_context,
                )
            )
        if (
            source is not None
            and isinstance(fake_e, FakeTensor)
            and (sym_val := fake_e.item_memo) is not None
        ):
            # Match the peephole in FakeTensorConverter.from_real_tensor that
            # strips FloatTensorSource before calling create_symbol.  Without
            # this, the tracked fake source name won't match source_to_var and
            # produce_guards_verbose will report "(unknown source)".
            if isinstance(source, FloatTensorSource):
                item_source = source.base
            else:
                item_source = CallMethodItemSource(source)
            tx.output.tracked_fakes.append(
                TrackedFake(sym_val, item_source, symbolic_context)
            )

        if is_traceable_wrapper_subclass(fake_e):
            attrs, _ = fake_e.__tensor_flatten__()
            for attr in attrs:
                fake_inner = getattr(fake_e, attr)
                inner = getattr(e, attr)
                inner_source = AttrSource(source, attr)
                wrap_to_fake_tensor_and_record(
                    inner,
                    tx,
                    source=inner_source,
                    is_tensor=isinstance(fake_inner, torch.Tensor),
                    parent_context=symbolic_context,
                )

        tx.output.tracing_context.tensor_to_context[e] = symbolic_context
        if is_sparse_any(fake_e):
            # TODO: for TensorGuards, this eventually may need more
            #       fields for the size/stride of any other constituents
            values = fake_e._values() if fake_e.is_sparse else fake_e.values()
            tx.output.input_source_to_sizes_strides[source] = {
                "size": fake_e.size(),
                # TODO: revise this, but for now this stride instead of ()
                #       avoids SegFault with PYTORCH_TEST_WITH_DYNAMO=1
                "stride": (1,) * fake_e.ndim,
                "values_size": values.size(),
                "values_stride": values.stride(),
            }
        else:
            tx.output.input_source_to_sizes_strides[source] = {
                "size": fake_e.size(),
                "stride": fake_e.stride(),
            }

        if (
            is_tensor
            and not (static_shapes and source.is_specialized_nn_module())
            and not is_constant_source(source)
        ):
            tx.output.tracked_fakes.append(
                TrackedFake(fake_e, source, symbolic_context)
            )
            tx.output.tracked_fakes_id_to_source[id(e)].append(source)

        return fake_e
    else:
        return e