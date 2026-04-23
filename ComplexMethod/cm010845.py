def _functionalized_f_helper(
        *args: list[FxValue],
    ) -> tuple[tuple[list[FxValue], list[Tensor]], list[AOTOutput | None]]:
        with maybe_enable_thunkify():
            # See Note [Disabling Functionalize TLS Above Python Functionalization]
            disable_above = torch._C._ExcludeDispatchKeyGuard(
                torch._C.DispatchKeySet(torch._C.DispatchKey.Functionalize)
            )

            with disable_above:
                # The functionalization code here can potentially trigger traces
                # into the graph, but we'd prefer to NOT do this, because if we
                # trace them now, we will end up with FX nodes that don't have
                # module stack annotations, which makes unflattener unhappy.
                # Wrap inputs into functional wrappers
                f_args = pytree.tree_map(to_fun, args)

                if trace_joint and has_input_mutated_in_graph and joint_fn_handle:
                    # TODO(ivankobzarev): Support fw and bw mutations for subclasses
                    def _post_forward(primals: Any) -> None:
                        nonlocal primals_after_forward
                        primals_after_forward = pytree.tree_map(from_fun, primals)
                        nonlocal f_args_after_forward
                        f_args_after_forward = f_args[0]
                        nonlocal f_args_mutation_counters_after_forward
                        f_args_mutation_counters_after_forward = [
                            MutationCounters(-1, -1, -1)
                            if not inputs_mutated_in_graph[i]
                            else _get_mutation_counters(f_arg)
                            for i, f_arg in enumerate(f_args_after_forward)
                        ]

                    joint_fn_handle.post_forward = _post_forward

                # Run the joint
                f_outs, f_outs_descs = call_and_expect_output_descs(fn, f_args)

            if trace_joint:
                # We support a limited amount of mutation of graph inputs during the backward pass.
                # (This is used e.g. by Float8, which needs to update buffers during the backward pass)
                # Here, we perform extra checks for primals that were mutated in the **backward**
                # We're doing the checks here instead of doing them with the rest of the input mutation handling because:
                # - We need to detect inputs that were mutated in the backward **separately** from mutations that happened
                #   during the forward, because the handling is different: some input mutations from the forward
                #   can be only handled in a fw-only runtime epilogue, and in theory if we wanted to handle those same
                #   types of mutations in the backward we would need a bw-only runtime epilogue.
                # - We could in theory have our analysis pass differentiate mutations in the fw from mutations in
                #   the bw by running our analysis first on the fw-only graph, and then on the joint graph. This would
                #   require an extra round of tracing though, so it's more efficient to do in-line here.
                if not (
                    isinstance(args, tuple)
                    and len(args) == 2
                    and isinstance(args[0], (list, tuple))
                ):
                    raise AssertionError(
                        f"expected args to be tuple of (list/tuple, ...), got {type(args)}"
                    )
                # Only look at mutations that happened to forward inputs (e.g. fw buffers that were saved for bw)
                primals_before = args[0]
                primals_after = pytree.tree_map(from_fun, f_args[0])
                for idx, (f_inpt, before, after, inpt_info) in enumerate(
                    zip(f_args[0], primals_before, primals_after, meta.input_info)
                ):
                    # Store information about mutations in joint(for backward analysis)
                    joint_mutates_data = has_data_mutation(f_inpt)

                    joint_mutates_metadata = has_metadata_mutation(
                        f_inpt, before, check_only_storage_mutation=False
                    )

                    # Ban metadata mutations on fw inputs during the bw
                    if not inpt_info.mutates_metadata:
                        if joint_mutates_metadata:
                            raise AssertionError(
                                "Found a graph input that had its metadata mutated in the backward. This is not supported"
                            )

                    # Ban storage resizing on fw inputs during the bw
                    if not inpt_info.mutation_inductor_storage_resize:
                        if was_inductor_storage_resized(f_inpt):
                            raise AssertionError(
                                "Found a graph input that had storage resizing in the backward. This is not supported"
                            )

                    # Allow data mutations on fw inputs during the bw, but only if they do not require grad
                    # So we can guarantee that we can keep the mutations in the graph
                    if (
                        joint_mutates_data
                        and not inpt_info.mutates_data
                        and not inpt_info.mutates_storage_metadata
                    ):
                        # Not banning here mutations on inpt_info.requires_grad -
                        # we'll check at runtime and fail only when backward is under torch.is_grad_enabled (create_graph)
                        # Add node meta for copy_ for partitioner that this node should be in backward graph.
                        with (
                            torch.fx.traceback.preserve_node_meta(),
                            set_partitioner_tag_must_be_in_backward(),
                        ):
                            # before and after should be tensors if we're calling copy_ on them
                            if not (
                                isinstance(before, torch.Tensor)
                                and isinstance(after, torch.Tensor)
                            ):
                                raise AssertionError(
                                    f"expected both before and after to be Tensors, got {type(before)} and {type(after)}"
                                )
                            # no_grad prevents the FakeTensor's requires_grad from
                            # triggering check_inplace during tracing.  The
                            # requires_grad case is checked at runtime instead
                            with torch.no_grad():
                                before.copy_(after)
                        meta.indices_of_inputs_that_requires_grad_with_mutations_in_bw.append(
                            idx
                        )
                # Now that we covered mutations to *forward* inputs during the backward,
                # we also need to cover mutations to *backward-only* inputs during the backward (e.g. mutation to a grad_out).
                # Today, we will just error in all cases of this happening unless someone needs us to support it.
                tangents_before = args[1]
                tangents_after = pytree.tree_map(from_fun, f_args[1])
                for f_inpt, before, after in zip(
                    f_args[1], tangents_before, tangents_after
                ):
                    if has_metadata_mutation(
                        f_inpt, before, check_only_storage_mutation=False
                    ):
                        raise AssertionError(
                            "Found an input to the backward that had metadata mutated "
                            "during the backward pass. This is not supported"
                        )
                    if has_data_mutation(f_inpt):
                        can_be_in_graph = _check_if_mutation_can_be_in_graph(
                            keep_input_mutations=True,
                            mutates_data=True,
                            mutates_metadata=False,
                            mutations_hidden_from_autograd=are_all_mutations_hidden_from_autograd(
                                f_inpt
                            ),
                            mutations_under_no_grad_or_inference_mode=are_all_mutations_under_no_grad_or_inference_mode(
                                f_inpt
                            ),
                            mutates_storage_metadata=False,
                            mutation_inductor_storage_resize=was_inductor_storage_resized(
                                f_inpt
                            ),
                            requires_grad=f_inpt.requires_grad,
                        )
                        if not can_be_in_graph:
                            raise AssertionError(
                                "a backward input that had data mutated in an autograd-aware way. This is not supported"
                            )
                        # Perform the input mutation
                        with torch.fx.traceback.preserve_node_meta():
                            # before and after should be tensors if we're calling copy_ on them
                            if not (
                                isinstance(before, torch.Tensor)
                                and isinstance(after, torch.Tensor)
                            ):
                                raise AssertionError(
                                    f"expected both before and after to be Tensors, got {type(before)} and {type(after)}"
                                )
                            before.copy_(after)

            if aot_config.keep_inference_input_mutations:
                # Note: This is a bit annoying. There's a layering issue here, where:
                # (1) functionalization needs to operate on **synthetic base** inputs, before unpacking them into the "real" inputs.
                # (2) For keep_input_mutations, we support tracing a call to copy_() directly on mutated inputs.
                #     However, we **only** want to support this for inputs that have data-only (and no metadata) mutations,
                #     because inductor (and backends in generally) would prefer not to see these (e.g. as_strided_(), resize_()).
                #     This makes it pretty difficult for this logic to operate on synthetic bases.
                # (3) In addition, there are cases where it's significantly cheaper to perform the copy on the individual
                #     (unpacked) input aliases, instead of the synthetic base.
                # Example case where (3) could be important:
                #
                #     def f(x, y):
                #         x.mul_(2)
                #         y.mul_(3)
                #         return x, y
                #    a = torch.ones(1'000'000)
                #    x, y = out(a[0:9], a[1:10])
                #
                # It would be much better to add copy_() calls into the graph for the two tiny slices, instead of materializing
                # a giant "updated synthetic base" and copying into a's entire storage.
                #
                # For now, we are pessimistically not performing the optimization from (3);
                # we will materialize an "updated" synthetic base, and copy it back to the synthetic input base.
                # This allows us to factor aot autograd much more nicely, since only one area of the code needs to worry
                # about synthetic bases.

                # Apply in graph forward mutations only in joint case.
                # Note: Mutations of primals in forward AND backward.
                # If we have mutations of the same input in forward and in backward,
                # we can not fuse them into one copy_ node. As in this case partitioner will put it
                # either in forward or in backward. This will lead to incorrect state
                # after forward and before backward.
                # We have to emit two copy_ nodes, marking with additional meta each node,
                # if it must be in forward or backward.
                # We memorize mutation counter of the inputs after forward.
                # Based on this after joint graph we check if backward also mutated input or not.
                # We emit copy_ only in the end of joint tracing, to provide invariant for joint
                # graph passes, that our graph is functional, except only some number of copy_ nodes
                # in the end.
                mcs_applied: list[MutationCounters] = [MutationCounters(0, 0, 0)] * len(
                    meta.input_info
                )
                if f_args_mutation_counters_after_forward is not None:
                    primals_before = args[0]
                    for idx, (f_inpt, before, after, inpt_info) in enumerate(
                        # pyrefly: ignore [no-matching-overload]
                        zip(
                            f_args_after_forward,  # type: ignore[arg-type]
                            primals_before,  # type: ignore[arg-type]
                            primals_after_forward,  # type: ignore[arg-type]
                            meta.input_info,
                        )
                    ):
                        if inpt_info.mutation_type != MutationType.MUTATED_IN_GRAPH:
                            continue

                        mcs_after_forward = f_args_mutation_counters_after_forward[idx]
                        with (
                            torch.fx.traceback.preserve_node_meta(),
                            set_partitioner_tag_must_be_in_forward(),
                            _proxy_tensor_disable_update_tensor_tracker(),
                        ):
                            apply_in_graph_mutations(
                                inpt_info,
                                # pyrefly: ignore [bad-argument-type]
                                before,
                                after,
                                f_inpt,
                                idx,
                                mcs_after_forward,
                                mcs_applied[idx],
                            )
                            mcs_applied[idx] = mcs_after_forward

                for idx, (inpt_old, f_inpt) in enumerate(
                    zip(args, f_args) if not trace_joint else zip(args[0], f_args[0])  # type: ignore[arg-type]
                ):
                    if not isinstance(f_inpt, torch.Tensor):
                        continue
                    if not is_fun(f_inpt):
                        raise AssertionError(
                            f"expected functional tensor, got {type(f_inpt)}"
                        )
                    inpt_new = from_fun(f_inpt)
                    if (
                        meta.input_info[idx].mutation_type
                        != MutationType.MUTATED_IN_GRAPH
                    ):
                        continue
                    mcs: MutationCounters | None = None
                    if f_args_mutation_counters_after_forward is not None:
                        # This could happen for subclasses tracing
                        # Subclasses support for mutations in fw and bw is TBD.
                        mcs = _get_mutation_counters(f_inpt)
                        if mcs == mcs_applied[idx]:
                            # No mutation in backward; mutation was already applied.
                            continue

                    with (
                        torch.fx.traceback.preserve_node_meta(),
                        set_partitioner_tag_must_be_in_backward(),
                    ):
                        apply_in_graph_mutations(
                            meta.input_info[idx],
                            # pyrefly: ignore[bad-argument-type]
                            inpt_old,
                            # pyrefly: ignore[bad-argument-type]
                            inpt_new,
                            f_inpt,
                            idx,
                            mcs,
                            mcs_applied[idx],
                        )

                # When an output tensor is a functionalized mutated input, and we
                # were able to move the mutation in to the graph then we can return
                # the mutated input directly. This prevents duplicating the
                # tensors contents.
                flat_outs, outs_spec = pytree.tree_flatten(f_outs)
                flat_outs = [from_fun(o) for o in flat_outs]
                num_outs = len(meta.output_info)

                for i in range(num_outs):
                    info = meta.output_info[i]
                    if info.output_type != OutputType.is_input:
                        continue

                    if info.base_idx is None:
                        raise AssertionError("info.base_idx must not be None")
                    if (
                        meta.input_info[info.base_idx].mutation_type
                        == MutationType.MUTATED_IN_GRAPH
                    ):
                        fw_args = args[0] if trace_joint else args
                        flat_outs[i] = fw_args[info.base_idx]
                return pytree.tree_unflatten(flat_outs, outs_spec), f_outs_descs

            return pytree.tree_map(from_fun, f_outs), f_outs_descs