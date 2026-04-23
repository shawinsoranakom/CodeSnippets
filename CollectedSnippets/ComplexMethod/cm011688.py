def _run(self, new_inputs: list[InputType], function_id: FunctionID) -> OutputType:
        # we will try to end the current execution lazily, since
        # we dont want to do unnecessary checking of the existing outputs
        # on the hot path, but both recording and warmup only happen once
        # so we check up front
        if self.in_recording:
            self.try_end_curr_recording(function_id)

        if self.in_warmup:
            self.try_end_curr_warmup(function_id)

        node_id = self._get_node_id()
        if function_id not in self.non_cudagraph_managed_mutation_hint[node_id]:
            self._update_non_cudagraph_managed_mutation(function_id, new_inputs)

        # Early exit if the function mutates inputs which are neither parameters/buffers nor
        # cudagraph recorded tensors. This check should happen after `try_end_curr_recording`
        # and `try_end_curr_warmup` which may change self.current_node.
        if self.non_cudagraph_managed_mutation_hint[node_id][
            function_id
        ] or self.exceed_rerecord_limit(node_id, function_id):
            return self.ids_to_funcs[function_id].model(new_inputs)

        # warming up a function and subsequentally recording may use different memory addresses
        # because both depend on the state of the caching allocator. if we warm up graph A,
        # then warm up graph B and make more allocations, the subsequent recording of A will not
        # necessarily use the same addresses as in the warm up. Thus any warm up of a node can only
        # be followed by warm up runs.
        if (
            (
                not (
                    function_id in self.warmed_up_functions
                    or config.triton.skip_cudagraph_warmup
                )
            )
            or self.in_warmup
            or config.triton.force_cudagraphs_warmup
        ):
            # If we are in the middle of executing cuda graphs, then we need to checkpoint memory state.
            # Both Recording and Warmup will be reflected in the allocator and dont need changes
            if self.path_state == ExecutionState.EXECUTION:
                self.apply_checkpoint_execution_state_in_allocator()

            return self.run_eager(new_inputs, function_id)

        assert not isinstance(self.current_node, CUDAWarmupNode)
        child_nodes = (
            self.roots if self.current_node is None else self.current_node.children
        )

        if not self.in_recording:
            unexpected_rerecord = False
            unexpected_rerecord_reason = None
            for child in child_nodes[function_id]:
                # here we are checking memory consistency between recording and execution,
                # as well as things like stability of tensor locations, etc
                # and other
                status, status_logger = child.check_invariants(new_inputs)
                if status == CheckInvariantStatus.SUCCESS:
                    return self.execute_node(child, new_inputs)

                if (
                    status == CheckInvariantStatus.StaticInputIdxMismatch
                    or status == CheckInvariantStatus.CudagraphManagedIdxMismatch
                ):
                    unexpected_rerecord = True
                    # Only compute detailed reason when debug logging is enabled
                    if log.isEnabledFor(logging.DEBUG):
                        unexpected_rerecord_reason = status_logger()
                        log.debug(
                            "[%s] Re-recording function=%s, mode=%s, reason=%s",
                            self.compile_id,
                            self.get_func_name(function_id),
                            self.id_to_mode[function_id].name,
                            unexpected_rerecord_reason,
                        )
                    else:
                        # Defer reason computation until needed (for exceed_rerecord_limit)
                        unexpected_rerecord_reason = status_logger

            # now that we know the new function can't be run as a child of the
            # current node, if it is a root, try to end the current execution.
            # as noted above, we want to do this lazily to avoid having to
            # check all existing outputs
            if self.current_node is not None and function_id in self.roots:
                self.try_end_curr_execution()

                # run again to hit the root matching case which must succeed
                if self.current_node is None:
                    return self.run(new_inputs, function_id)

            if len(self.ids_to_funcs[function_id].mutated_input_idxs) > 0:
                self._update_non_cudagraph_managed_mutation(function_id, new_inputs)
                if self.non_cudagraph_managed_mutation_hint[self._get_node_id()][
                    function_id
                ]:
                    return self.ids_to_funcs[function_id].model(new_inputs)

            # nb: run before checkpointing because checkpointing is slow, and we will
            # be using the eager caching allocator pool which does not require live
            # accounting of tensors in cudagraph allocator
            if unexpected_rerecord:
                curr_node_id = self._get_node_id()
                self.num_rerecord[curr_node_id][function_id] += 1
                if self.exceed_rerecord_limit(curr_node_id, function_id):
                    _id = curr_node_id.id if curr_node_id else None
                    # unexpected_rerecord_reason is either a string (if debug was enabled)
                    # or a callable (if debug was disabled)
                    assert unexpected_rerecord_reason is not None
                    reason = (
                        unexpected_rerecord_reason
                        if isinstance(unexpected_rerecord_reason, str)
                        else unexpected_rerecord_reason()
                    )
                    log_cudagraph_skip_and_bump_counter(
                        f"skipping cudagraph due to function {function_id.id} exceeding max "
                        f"re-recording limit "
                        f"(={torch._inductor.config.triton.cudagraph_unexpected_rerecord_limit}) "
                        f"on cudagraph node {_id} due to {reason}."
                    )
                    return self.ids_to_funcs[function_id].model(new_inputs)

            # at this point, we necessarily will do a new recording
            self.debug_fail_counter += 1

            self.try_end_curr_execution()
            if self.current_node is not None:
                self.apply_checkpoint_execution_state_in_allocator()

        # now, we are in a recording state !
        return self.record_function(new_inputs, function_id)