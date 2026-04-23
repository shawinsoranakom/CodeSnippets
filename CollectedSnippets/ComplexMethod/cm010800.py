def __post_init__(self) -> None:
        # pre-compute the indices of the inputs that are mutated.
        # When keep_input_mutations is set, we don't need to worry about our epilogue
        # handling data-only mutations, because we keep them directly in the graph.
        mutated_inp_runtime_indices = [
            i
            for i, m in enumerate(self.input_info)
            if (m.mutation_type == MutationType.MUTATED_OUT_GRAPH)
        ]

        mutated_graph_handled_indices = [
            i
            for i, m in enumerate(self.input_info)
            if m.mutation_type == MutationType.MUTATED_IN_GRAPH
        ]
        self.mutated_graph_handled_indices = mutated_graph_handled_indices
        self.num_mutated_graph_handled_indices = len(self.mutated_graph_handled_indices)

        mutated_graph_handled_indices_seen_by_autograd = [
            i
            for i in mutated_graph_handled_indices
            if not self.input_info[i].mutations_hidden_from_autograd
        ]

        self.mutated_graph_handled_indices_seen_by_autograd = (
            mutated_graph_handled_indices_seen_by_autograd
        )
        self.num_mutated_graph_handled_indices_seen_by_autograd = len(
            self.mutated_graph_handled_indices_seen_by_autograd
        )

        aliased_out_indices = [
            i
            for i, m in enumerate(self.output_info)
            if m.output_type
            not in [
                OutputType.non_alias,
                OutputType.unsafe_view_alias,
                OutputType.custom_function_view,
            ]
        ]
        unsafe_view_out_indices = [
            i
            for i, m in enumerate(self.output_info)
            if m.output_type is OutputType.unsafe_view_alias
        ]

        # This is pre-computed in post_init for perf.
        # It contains the index of every element
        # of input_info that corresponds to a mutation (data or metadata or both)
        self.mutated_inp_runtime_indices = mutated_inp_runtime_indices
        self.num_mutated_inp_runtime_indices = len(self.mutated_inp_runtime_indices)

        # This is pre-computed for perf.
        # It contains the index of every element
        # of output_info that corresponds to an alias (either of an input or intermediate)
        self.aliased_out_indices = aliased_out_indices
        self.unsafe_view_out_indices = unsafe_view_out_indices
        self.num_outputs = len(self.output_info)
        self.num_outputs_non_aliased = len(
            [
                x
                for x in self.output_info
                if x.output_type
                in [
                    OutputType.non_alias,
                    OutputType.unsafe_view_alias,
                    OutputType.custom_function_view,
                ]
            ]
        )
        self.num_outputs_aliased_to_inputs = len(
            [
                x
                for x in self.output_info
                if x.output_type
                in [
                    OutputType.alias_of_input,
                    OutputType.is_input,
                ]
            ]
        )
        self.num_unsafe_view_outputs = len(self.unsafe_view_out_indices)
        self.num_outputs_aliased_to_intermediates = len(
            [
                x
                for x in self.output_info
                if x.output_type
                in [
                    OutputType.alias_of_intermediate,
                    OutputType.alias_of_intermediate_save_as_output,
                    OutputType.alias_of_intermediate_base_is_user_output,
                ]
            ]
        )
        self.num_outputs_aliased = (
            self.num_outputs_aliased_to_inputs
            + self.num_outputs_aliased_to_intermediates
        )

        # Record dynamic outputs of the Dynamo traced forward graph
        # Mark them as dynamic at the end of the runtime wrapper
        self.dynamic_outputs = any(o.dynamic_dims for o in self.output_info)

        # Record the indices of dynamic outputs in the partitioned forward graph
        # Mark them as dynamic in the runtime wrapper
        # activation index -> dynamic dims indices
        self.dynamic_saved_tensors_idxs: dict[int, set[int]] = {}

        # See Note: [AOTAutograd Backward Guards]
        # This is pre-computed for fast asserts on the types of our grad_outputs in the backward.
        # Eventually, we should kill this and replace with real backward guards.
        # (we want to precompute the "runtime" types, so replace FakeTensor with torch.Tensor)
        self.output_types = [
            torch.Tensor if isinstance(x, FakeTensor) else type(x)
            for x in self.traced_tangents
        ]

        self.is_rng_op_functionalized = config.functionalize_rng_ops
        # All of the above metadata is collected by tracing the fw function.
        # However, extra outputs for rng offsets behave differently. Both fwd
        # and bwd graphs have their own outputs for the total consumed offsets.
        # Unlike mutated inputs, we don't have to worry about sending the right
        # set of tensors between fwd and bwd. Fwd and bwd offsets are
        # independent and simpler to handle. Therefore, we track them
        # separately.
        self.num_outputs_rng_offset = 1 if self.is_rng_op_functionalized else 0

        # Our forward() returns both (tokens, mutated_inputs, outputs, output_intermediate_bases, saved_tensors, saved_symints)
        # Tokens will be split out before mutations/view handling and we do not count them here.
        self.num_forward_returns = (
            self.num_mutated_inp_runtime_indices
            + self.num_outputs
            + self.num_intermediate_bases
        )
        # In case of functionalization of rng ops, the fw_module returns one
        # additional output for rng offset. This rng offset is used right
        # away to advance the rng state, and is not passed on to the raw
        # outputs. However, we need to know the exact boundary to identify
        # which tensors to be saved for the bwd graph.  num_forward captures
        # this information.
        self.num_forward = self.num_forward_returns + self.num_outputs_rng_offset