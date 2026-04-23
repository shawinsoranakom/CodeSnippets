def run_node(self, n: torch.fx.Node) -> object:
        """Lower and execute a single FX node into Inductor IR."""

        def debug(msg: str) -> None:
            log.debug("lowering %s %s", LazyString(n.format_node), msg)  # type: ignore[arg-type]

        # Use channels-last stride order for certain
        # dense 4D intermediates when layout optimization determines a
        # downstream consumer (typically conv) prefers channels-last.
        def maybe_apply_channels_last_stride_order(
            result: ir.IRNode, n: torch.fx.Node
        ) -> ir.IRNode:
            dense = torch._prims_common.is_non_overlapping_and_dense_or_false(
                n.meta["val"]
            )
            strides = n.meta["val"].stride()
            unbacked_symbols_in_strides = len(free_unbacked_symbols(strides)) > 0
            if (
                not unbacked_symbols_in_strides
                and dense
                and len(result.get_size()) == 4
                and n in self.nodes_prefer_channels_last
                and not is_user_visible
                and not is_input_for_as_strided
            ):
                result = ir.ExternKernel.require_stride_order(
                    result,
                    ir.get_stride_order(
                        make_channels_last_strides_for(n.meta["val"].shape)
                    ),
                )
            return result

        from torch._inductor.compiler_bisector import CompilerBisector

        buffer_watermark = len(self.buffers)
        operation_watermark = len(self.operations)

        # origins: OrderedSet[Union[Node, ir.IRNode]] = OrderedSet([n])
        origins: OrderedSet[Any] = OrderedSet([n])
        is_call_function = n.op == "call_function"
        if is_call_function:
            args, kwargs = self.fetch_args_kwargs_from_env(n)
            origins |= gather_origins(args, kwargs)
            self._realize_inputs_at_stream_boundaries(n)
        with (
            ir.IRNode.current_origins(origins),
            ir.IRNode.current_stream_idx(self._get_node_stream(n)),
            self.set_current_node(n),
            V.set_current_node(n),
        ):
            if (
                n.op == "call_function"
                # this path only for built-in operators
                and n.target
                and isinstance(n.target, torch._ops.OpOverload)
                and torch._library.utils.is_builtin(n.target)
                and (
                    fallback_node_due_to_unsupported_type(n)
                    or CompilerBisector.disable_subsystem(
                        "inductor", "lowerings", lambda: repr(n)
                    )
                )
            ):
                debug("fallback_handler")
                result = fallback_handler(n.target, add_to_fallback_set=False)(
                    *args,  # type: ignore[possibly-undefined]
                    **kwargs,  # type: ignore[possibly-undefined]
                )
            elif (
                n.op == "call_function"
                and isinstance(
                    n.target, (torch._ops.OpOverload, torch._ops.HigherOrderOperator)
                )
                and should_fallback_by_default(n)
            ):
                # this path supports fallback due to inductor lite mode. It supports
                # both OpOverload and HOPs (e.g., triton_kernel_wrapper_functional).
                debug("fallback_handler")
                result = fallback_handler(n.target, add_to_fallback_set=False)(
                    *args,  # type: ignore[possibly-undefined]
                    **kwargs,  # type: ignore[possibly-undefined]
                )
            elif (
                n.op == "call_function"
                and n.target is torch.ops.higher_order.triton_kernel_wrapper_mutation
                and config.triton_kernel_default_layout_constraint != "flexible_layout"
            ):
                debug("user_defined_triton_kernel_layout_constraints")
                if (
                    config.triton_kernel_default_layout_constraint
                    == "needs_fixed_stride_order"
                ):
                    old_args = args  # type: ignore[possibly-undefined]
                    old_kwargs = kwargs  # type: ignore[possibly-undefined]

                    if eager_input_vals := n.meta.get("eager_input_vals"):
                        inp_args = eager_input_vals[0]
                        inp_kwargs = eager_input_vals[1]
                        args, kwargs = constrain_to_fake_tensors(
                            # pyrefly: ignore [unbound-name]
                            args,
                            # pyrefly: ignore [unbound-name]
                            kwargs,
                            inp_args,
                            inp_kwargs,
                        )
                    else:
                        args, kwargs = constrain_to_fx_strides(n, *args, **kwargs)  # type: ignore[index]
                    result = self.call_function(n.target, args, kwargs)  # type: ignore[arg-type]
                    self.propagate_mutation(n, old_args, old_kwargs, args, kwargs)  # type: ignore[possibly-undefined]
                else:
                    raise RuntimeError(
                        f"Unknown triton_kernel_default_layout_constraint: {config.triton_kernel_default_layout_constraint}"
                    )
            elif is_magic_method(n.target):
                # TODO: this is sus, it probably should be handled in the
                # lowerings themselves similarly to sym_size/sym-stride
                # https://github.com/pytorch/pytorch/issues/127789
                debug("is_magic_method")
                if isinstance(
                    n.meta["val"], (torch.SymInt, torch.SymFloat, torch.SymBool)
                ):
                    result = n.meta["val"].node.expr
                else:
                    result = super().run_node(n)
            else:
                debug("")
                result = super().run_node(n)

            # require the same stride order for dense outputs,
            # 1. user-land view() will not throw because inductor
            # output different strides than eager
            # long term the solution is to make view() always succeed
            # with infallible strides.
            # 2: as_strided ops, we need make sure its input has same size/stride with
            # eager model to align with eager behavior.
            as_strided_ops = [
                torch.ops.aten.as_strided.default,
                torch.ops.aten.as_strided_.default,
                torch.ops.aten.as_strided_scatter.default,
                torch.ops.aten.resize.default,
                torch.ops.aten.resize_as.default,
            ]
            is_output = any(user.op == "output" for user in n.users)
            is_user_visible = n in self.user_visible_output_strides
            is_input_for_as_strided = any(
                user.target in as_strided_ops for user in n.users
            )

            if n.meta.get("inductor_realize_to_strides", False) and isinstance(
                result, TensorBox
            ):
                result.realize()
                strides = n.meta["val"].stride()
                sym_strides = torch._inductor.utils.any_is_symbolic(*strides)
                if result.maybe_get_stride() != strides and not sym_strides:
                    stride_order = ir.get_stride_order(strides)
                    result = ir.ExternKernel.require_stride_order(result, stride_order)
            if (
                is_output
                and isinstance(result, TensorBox)
                and isinstance(result.data, ir.BaseView)
            ):
                # Realize so that outputs are correctly aliased
                result.realize()

            if (is_output or is_input_for_as_strided) and isinstance(
                n.meta.get("val"), torch.Tensor
            ):
                if is_user_visible:
                    strides = self.user_visible_output_strides.get(n)
                else:
                    strides = n.meta["val"].stride()

                if strides is not None and len(strides) > 0:
                    allow_padding = (
                        config.pad_outputs or not is_user_visible
                    ) and not is_input_for_as_strided
                    dense = torch._prims_common.is_non_overlapping_and_dense_or_false(
                        n.meta["val"]
                    )
                    unbacked_symbols_in_strides = (
                        len(free_unbacked_symbols(strides)) > 0
                    )
                    if (
                        not unbacked_symbols_in_strides
                        and dense
                        and len(result.get_size()) == 4
                        and n in self.nodes_prefer_channels_last
                        and not is_user_visible
                        and not is_input_for_as_strided
                    ):
                        strides = ir.FlexibleLayout.stride_ordered_for_memory_format(
                            result.get_size(), torch.channels_last
                        )
                    if not unbacked_symbols_in_strides and len(strides):
                        # To avoid converting possible view ops to a copy kernel, we use the previous
                        # require_exact_strides to handle views. But ultimately it's better to require
                        # the right strides at the tensor definition.
                        if n.meta["val"]._is_view() or isinstance(
                            result.data,
                            ir.BaseView,
                        ):
                            result = ir.ExternKernel.require_stride_order(
                                result,
                                ir.get_stride_order(strides),
                                allow_padding=allow_padding,
                            )
                        else:
                            # Fix for 0-d tensors: if result size is empty,
                            # strides should also be empty
                            if len(result.get_size()) == 0 and len(strides) > 0:
                                strides = []
                            result = ir.ExternKernel.require_exact_strides(
                                result, strides, allow_padding=allow_padding
                            )

            # Realize if (1) any user need inputs realized, or (2) there is
            # already too many reads and rematerializing can be bad.
            num_users = len(OrderedSet(n.users))
            if num_users > 1 and isinstance(result, TensorBox):
                for user in n.users:
                    if user.target in needs_realized_inputs:
                        result.realize_hint()
                        # This inclusion is somewhat controversial (from
                        # discussion between Horace, Natalia, and Elias).
                        # Currently, it's not very clear why this is helpful.
                        # The general idea here is that even though a node may
                        # have FlexibleLayout, we still often *treat* it as if
                        # it was contiguous. This appears to sometimes result in
                        # suboptimal behavior.
                        #
                        # When we do a better job selecting layout, we should
                        # revisit this.
                        need_fixed_layout = [
                            torch.ops.aten.convolution_backward.default,
                            torch.ops.aten.mm.default,
                            torch.ops.aten._int_mm.default,
                        ]
                        need_fixed_channels_last_layout = []
                        if not self.layout_opt:
                            need_fixed_layout.append(torch.ops.aten.convolution.default)
                        if torch._C._has_mkldnn:
                            need_fixed_layout += [
                                torch.ops.mkldnn._linear_pointwise.default,
                                torch.ops.mkldnn._linear_pointwise.binary,
                                torch.ops.aten.mkldnn_rnn_layer.default,
                                torch.ops.onednn.qlinear_pointwise.default,
                                torch.ops.onednn.qlinear_pointwise.tensor,
                                torch.ops.onednn.qlinear_pointwise.binary,
                                torch.ops.onednn.qlinear_pointwise.binary_tensor,
                            ]
                            need_fixed_channels_last_layout += [
                                torch.ops.mkldnn._convolution_pointwise.default,
                                torch.ops.mkldnn._convolution_pointwise.binary,
                                torch.ops.mkldnn._convolution_pointwise_.binary,
                                torch.ops.mkldnn._convolution_transpose_pointwise.default,
                                torch.ops.onednn.qconv_pointwise.default,
                                torch.ops.onednn.qconv2d_pointwise.binary,
                            ]
                            if torch._C.has_mkl:
                                need_fixed_layout += [torch.ops.mkl._mkl_linear.default]
                        if user.target in need_fixed_layout:
                            result = ir.ExternKernel.require_stride_order(
                                result,
                                ir.get_stride_order(n.meta["val"].stride()),
                                allow_padding=True,
                            )
                        if (
                            user.target in need_fixed_channels_last_layout
                            and n is user.args[0]
                        ):
                            result = ir.ExternKernel.require_stride_order(
                                result,
                                ir.get_stride_order(
                                    make_channels_last_strides_for(n.meta["val"].shape)
                                ),
                            )
                    if user.op == "output":
                        # pyrefly: ignore [missing-attribute]
                        if isinstance(result.data.data, (Pointwise, Reduction)):
                            # Cheap-to-recompute nodes (0 buffer reads, e.g.
                            # index arithmetic or constant fills) can be
                            # deferred to realize_input at output processing.
                            # This prevents cascade materialization where
                            # shared constants inflate downstream read counts.
                            if (
                                config.delay_realize_cheap_outputs
                                # pyrefly: ignore [missing-attribute]
                                and result.data.num_reads() == 0
                                # pyrefly: ignore [missing-attribute]
                                and not result.data.has_large_inner_fn()
                            ):
                                continue
                            result.realize()

                _data = result.data  # type: ignore[attr-defined]
                while not isinstance(_data, StorageBox) and isinstance(
                    _data, (ir.BaseView, ir.MutableBox)
                ):
                    _data = _data.data

                if isinstance(_data, StorageBox) and _data.should_realize_on_reuse(
                    len(n.users)
                ):
                    result = maybe_apply_channels_last_stride_order(result, n)

                # TODO(jansel): introduce a store vs inline choice
                result.mark_reuse(len(n.users))

            # Realize if the IRNode already has accumulated lots of reads
            if isinstance(result, TensorBox) and result.has_exceeded_max_reads():
                # Prevent excessive accumulation in a computed buffer, when
                # there are multiple branches each with small number of memory
                # reads, but they converge to a user.
                result = maybe_apply_channels_last_stride_order(result, n)
                result.realize_hint()

            # Realize if a Pointwise has too much stuff to be inlined.
            # As this may cause RecursionError during Inductor's evaluation.
            if isinstance(result, TensorBox) and isinstance(result.data, StorageBox):
                curr = result.data.data
                if isinstance(curr, Pointwise):
                    # Use inner fn as a rough proxy. Good enough.
                    if curr.has_large_inner_fn(threshold=100):
                        result.realize()

        assign_origin_node(result, n)
        self.register_users_of(result)

        new_unbacked_defs = OrderedSet[sympy.Symbol]()
        for buf in self.buffers[buffer_watermark:]:
            new_unbacked_defs |= buf.get_unbacked_symbol_defs()
        for op in self.operations[operation_watermark:]:
            new_unbacked_defs |= op.get_unbacked_symbol_defs()

        shape_env = V.graph.sizevars.shape_env

        # An input can be unbacked symint i.e.: when mark_unbacked is used.
        # in that case add it to new_unbacked_defs.
        if (
            n.op == "placeholder"
            and isinstance(result, sympy.Symbol)
            and shape_env.is_unbacked_symint(result)
        ):
            new_unbacked_defs.add(result)

        def format_new_defs() -> str:
            r = [
                f"unbacked_symbol_defs={buf.get_unbacked_symbol_defs()} in:\n{buf}\n"
                for buf in self.buffers[buffer_watermark:]
            ]
            r.extend(
                f"unbacked_symbol_defs={op.get_unbacked_symbol_defs()} in:\n{op}\n"
                for op in self.operations[operation_watermark:]
            )
            return "***\n".join(r)

        # We do not skip unbacked symints that are input for backward see the note below.
        if V.graph.is_backward and n.op == "placeholder":
            return result

        # Note [Backwards runtime asserts]
        # Backwards poses an interesting problem for deferred runtime
        # asserts.  In the easy case, we may solely close over data
        # dependent sized tensors, and there are no binding sites for
        # unbacked SymInts.  In this case, we can just drop all the
        # runtime asserts on the floor: no non-placeholder bindings, no
        # problem.
        #
        # However, it is *possible* for a fresh runtime assert to show up
        # between forwards and backwards.  Right now, the freezing process
        # that happens when we lower forwards means that we will freeze
        # runtime asserts, and then the moment the backwards lowering
        # process attempts to add a new deferred runtime assert, we will
        # fail.  Let's say you remove that assert.  Now when we get here,
        # we need to make sure we actually emit these asserts (because we
        # can't emit them in forwards, we already compiled it).  So we
        # have to do something here.  But we don't want to reemit ALL
        # deferred runtime asserts, we only want to emit the NEW ones.
        # Therefore needing some sort of stratification in the ShapeEnv.
        # This is all doable, it just hasn't been done yet.

        unbacked_bindings = resolve_unbacked_bindings(
            V.graph.sizevars.shape_env, n.meta.get("unbacked_bindings", {})
        )
        assert unbacked_bindings is not None
        # When we do lowering, it is possible we reallocate unbacked SymInts.
        # So we need to line up the unbacked SymInts when performing the test
        # here
        #
        # In principle, we could permit lowering to introduce MORE unbacked
        # SymInts: as long as all the old unbacked ones are accounted for,
        # it's fine for inductor to introduce extra calls to item()/unbacked()
        # whatever.  This actually happens in practice when an unbacked SymInt
        # gets memoized away; naively, when Inductor reprocesses a kernel, it
        # doesn't know that the memo still applies, and ends up allocating a
        # new symbol.  However, this is generally a bad thing: we may still
        # end up needing to test equalities on the symbols, and a fresh
        # symbol is likely to hit lots of GuardOnDataDependent errors that
        # we already know facts for.
        renamed_unbacked_bindings = OrderedSet(
            V.fake_mode.shape_env.unbacked_renamings.get(s, s)
            for s in unbacked_bindings
        )

        assert new_unbacked_defs >= renamed_unbacked_bindings, (
            f"failed {new_unbacked_defs} >= {renamed_unbacked_bindings} (inductor >= fx)\n"
            f"fx node is: {n.format_node()}\n"
            f"new operations are:\n\n{format_new_defs()}"
        )
        self.create_deferred_runtime_asserts(n, new_unbacked_defs)
        return result