def from_tracing_metadata(
        cls,
        *,
        in_spec: pytree.TreeSpec,
        out_spec: pytree.TreeSpec,
        graph_input_names: list[str],
        graph_output_names: list[str],
        view_mutation_metadata: ViewAndMutationMeta,
        named_parameters: list[str],
        named_buffers: list[str],
        num_user_inputs: int,
        num_user_outputs: int,
        trace_joint: bool,
        loss_index: int | None,
        backward_signature: BackwardSignature | None,
    ) -> GraphSignature:
        graph_inputs = graph_input_names
        graph_outputs = graph_output_names
        parameters = list(named_parameters)
        buffers = list(named_buffers)
        num_tokens = len(view_mutation_metadata.tokens)

        # Calling convention assumptions:
        # (1) graph inputs = (input_tokens, params, buffers, user_inputs)
        # (2) graph outputs = (output_tokens, mutated_inputs, user_outs, param_gradients)
        # (If we are capturing an inference graph, this convention is identical
        #  except that param_gradients is empty)
        # See Note [Side-Effectful Tokens in AOTAutograd] for information on tokens

        # Address input calling conventions:
        start, stop = 0, num_tokens
        input_tokens = graph_inputs[start:stop]

        start, stop = stop, stop + len(parameters)
        inputs_to_parameters = dict(zip(graph_inputs[start:stop], parameters))

        start, stop = stop, stop + len(buffers)
        inputs_to_buffers = dict(
            zip(
                graph_inputs[start:stop],
                buffers,
            )
        )

        start, stop = stop, stop + num_user_inputs
        user_inputs = graph_inputs[start:stop]

        # We should've gone through all the inputs now
        if len(graph_inputs) - stop != 0:
            raise AssertionError(
                f"expected all graph_inputs consumed, but {len(graph_inputs) - stop} remain"
            )

        # Address output calling conventions:
        start, stop = 0, num_tokens
        output_tokens = graph_outputs[start:stop]

        names = [*input_tokens, *parameters, *buffers, *user_inputs]
        mutations: list[str] = []
        for idx, input_info in enumerate(view_mutation_metadata.input_info):
            if input_info.mutates_data:
                if trace_joint:
                    # Only buffers can be mutated, not parameters
                    if idx < len(parameters):
                        raise AssertionError(
                            f"expected idx ({idx}) >= len(parameters) ({len(parameters)}) when tracing joint"
                        )
                mutations.append(names[idx + num_tokens])

        if len(mutations) != view_mutation_metadata.num_mutated_inp_runtime_indices:
            raise AssertionError(
                f"len(mutations) ({len(mutations)}) != "
                f"num_mutated_inp_runtime_indices ({view_mutation_metadata.num_mutated_inp_runtime_indices})"
            )

        start, stop = (
            stop,
            stop + view_mutation_metadata.num_mutated_inp_runtime_indices,
        )
        outputs_to_mutations = dict(zip(graph_outputs[start:stop], mutations))

        user_inputs_to_mutate: dict[GraphOutputName, GraphInputName] = {}
        buffers_to_mutate: dict[GraphOutputName, FQN] = {}
        parameters_to_mutate: dict[GraphOutputName, FQN] = {}
        for output_name, mutation_name in outputs_to_mutations.items():
            if mutation_name in user_inputs:
                # pyrefly: ignore [unsupported-operation]
                user_inputs_to_mutate[output_name] = mutation_name
            else:
                if mutation_name not in buffers and mutation_name not in parameters:
                    raise AssertionError(
                        f"mutation_name '{mutation_name}' not found in buffers or parameters"
                    )
                if mutation_name in buffers:
                    # pyrefly: ignore [unsupported-operation]
                    buffers_to_mutate[output_name] = mutation_name
                else:
                    # pyrefly: ignore [unsupported-operation]
                    parameters_to_mutate[output_name] = mutation_name

        start, stop = stop, stop + num_user_outputs
        user_outputs = graph_outputs[start:stop]

        unused_outputs = len(graph_outputs) - stop
        if backward_signature is not None:
            unused_outputs -= len(backward_signature.gradients_to_parameters) + len(
                backward_signature.gradients_to_user_inputs
            )
        if unused_outputs != 0:
            raise AssertionError(f"expected unused_outputs == 0, got {unused_outputs}")

        return GraphSignature(
            parameters=parameters,  # type: ignore[arg-type]
            buffers=buffers,  # type: ignore[arg-type]
            user_inputs=user_inputs,  # type: ignore[arg-type]
            user_outputs=user_outputs,  # type: ignore[arg-type]
            inputs_to_buffers=inputs_to_buffers,  # type: ignore[arg-type]
            inputs_to_parameters=inputs_to_parameters,  # type: ignore[arg-type]
            user_inputs_to_mutate=user_inputs_to_mutate,
            buffers_to_mutate=buffers_to_mutate,  # type: ignore[arg-type]
            parameters_to_mutate=parameters_to_mutate,  # type: ignore[arg-type]
            in_spec=in_spec,
            out_spec=out_spec,
            backward_signature=backward_signature,
            input_tokens=input_tokens,  # type: ignore[arg-type]
            output_tokens=output_tokens,  # type: ignore[arg-type]
        )