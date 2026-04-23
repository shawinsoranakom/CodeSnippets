def _aot_stage2b_bw_compile(
    bw_module: torch.fx.GraphModule,
    maybe_subclass_meta: SubclassMeta | None,
    fw_metadata: ViewAndMutationMeta,
    fwd_output_strides: list[tuple[int, ...] | None] | None,
    num_symints_saved_for_bw: int,
    aot_config: AOTConfig,
    # pyrefly: ignore [implicit-any]
) -> tuple[AutogradLazyBackwardCompileInfo, Callable | None]:
    """
    Compile the backward graph. Returns:
    - the placeholder list for the backward graph
    - the compiled backward function
    """
    with torch.no_grad():
        # NB: It's important to compile backwards ahead of time, as this may
        # add extra guards which we need to apply to the Dynamo cache at
        # forwards
        with track_graph_compiling(aot_config, "backward"), torch._C._DisableAutocast():
            placeholder_list = fx_placeholder_vals(bw_module)

            forward_saved_for_backwards_strides = None
            if fwd_output_strides is not None:
                inner_meta = _get_inner_meta(maybe_subclass_meta, fw_metadata)
                forward_saved_for_backwards_strides = fwd_output_strides[
                    inner_meta.tensors_saved_for_backwards_slice
                ]

            # saved activations can have different stride to eager if
            # the compiler does layout optimization. We should restride the
            # tensor passed in for compiling the backward graph using the
            # saved tensor's stride.
            for i in range(len(placeholder_list)):
                ph_arg = placeholder_list[i]
                if not isinstance(ph_arg, torch.Tensor):
                    continue

                if forward_saved_for_backwards_strides is None:
                    continue

                real_stride = None
                # Per all_args calling convention
                j = i - num_symints_saved_for_bw
                if 0 <= j < len(forward_saved_for_backwards_strides):
                    real_stride = forward_saved_for_backwards_strides[j]
                if real_stride is None:
                    continue

                # Comparing ph_arg.stride() with real_stride directly may
                # cause dynamic dimensions in ph_arg being specialized to static
                # value. Using suppress_guards and guard_or_true to avoid that.

                stride_different = False
                fake_mode = detect_fake_mode()
                suppress_ctx = (
                    fake_mode.shape_env.suppress_guards()
                    if fake_mode is not None and fake_mode.shape_env is not None
                    else nullcontext()
                )

                # Inductor can choose different strides for activations than
                # what backward graph has. if we can't statically tell that
                # strides are the same, we assume they are not.
                with suppress_ctx:
                    for k in range(len(ph_arg.stride())):
                        # real_stride can't be symbolic.

                        if guard_or_true(ph_arg.stride()[k] != int(real_stride[k])):
                            stride_different = True
                            break

                if stride_different:
                    # Note that here we use the stride of the real tensor to
                    # restride a FakeTensor. This does not cause trouble
                    # for dynamic shape since this code path only get
                    # executed if layout optimization is enabled. And we
                    # disable layout optimization for dynamic shape right
                    # now.
                    #
                    # A solution that decide stride order based on real
                    # tensor's stride and then apply that stride order to
                    # the FakeTensor does not work smoothly since some
                    # tensor's layout is not 'dense'. E.g. mixnet_l has a
                    # tensor with size [8, 64, 112, 112] and strides
                    # (2408448, 1, 21504, 192). The solution mentioned will
                    # decide a stride of (802816, 1, 7168, 64) for this
                    # tensor which is wrong.

                    ph_size = ph_arg.size()

                    placeholder_list[i] = ph_arg.as_strided(ph_size, real_stride)
            compiled_bw_func = None
            if (
                num_symints_saved_for_bw > 0
                or aot_config.force_non_lazy_backward_lowering
            ):
                try:
                    # See Note: [Backward graph lazy lowering]
                    with torch._subclasses.fake_tensor.unset_fake_temporarily():
                        # If bw_module contains lifted constants, they will be real tensors stored as
                        # GraphModule. Deepcopying tensors under fake mode is not supported and will
                        # raise when attempting to set storage.
                        bw_module_copy = copy.deepcopy(bw_module)
                    if aot_config.bw_compiler is None:
                        raise AssertionError("aot_config.bw_compiler must not be None")
                    compiled_bw_func = aot_config.bw_compiler(
                        bw_module_copy, placeholder_list
                    )
                    del bw_module_copy
                except Exception as e:
                    if aot_config.force_non_lazy_backward_lowering:
                        raise
                    exc = e
                    trace_structured(
                        "artifact",
                        metadata_fn=lambda: {
                            "name": "eager_compile_backwards_failure",
                            "encoding": "string",
                        },
                        payload_fn=lambda: "\n".join(
                            traceback.format_exception(
                                type(exc), exc, exc.__traceback__
                            )
                        ),
                    )
                    log.warning(
                        "failed to eagerly compile backwards for dynamic, suppressing in case backwards not needed",
                        exc_info=True,
                    )
            # Compiled autograd will run the bw_module in the backward pass,
            # so recompilation need happen anyway if the backward pass is ever
            # called.
            #
            # The reason we do the GraphModule recompilation here is because
            # the lazy recompilation will cause issue in the backward pass
            # with compiled autograd.
            #
            # Do the _LazyGraphModule.force_recompile here rather than when
            # bw_module is first generated by the partitioner because the bw_module.recompile
            # may be called in some code path later and cause the _LazyGraphModule.forward
            # becomes the lazy version again. One example is when dynamic shape is enabled
            # upfront, the bw_compiler will be called above which can cause extra
            # graph module recompilation on bw_module.
            if torch._dynamo.compiled_autograd.in_compiled_autograd_region:
                from torch.fx._lazy_graph_module import _LazyGraphModule

                _LazyGraphModule.force_recompile(bw_module)

            saved_context = TracingContext.try_get()
            saved_compile_context = CompileContext.try_get()

            lazy_backward_info = AutogradLazyBackwardCompileInfo(
                # pyrefly: ignore [bad-argument-type]
                bw_module,
                placeholder_list,
                saved_context,
                saved_compile_context,
            )

            return lazy_backward_info, compiled_bw_func