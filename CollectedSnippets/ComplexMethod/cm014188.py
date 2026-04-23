def _call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        """
        Goal of this function is to rewrite local_map usage as a HOP:
            local_map(func, ...) -> local_map_hop(gm, ...)
        """

        (
            user_func,
            out_placements,
            in_placements,
            in_grad_placements,
            device_mesh,
            redistribute_inputs,
            *user_args,
        ) = args

        # None placements are used to pass non-Tensors into the local_map function.
        # Containers passed this way can not hold tensors. Thus, Dynamo would have inlined
        # into them, and we handle None placements by assuming they will be desugared away.
        # This will need to be adjusted for dynamic shapes support.
        def check_none_last(placements: Sequence[Any | None]) -> int:
            seen_none = 0
            for p in placements:
                if p is None:
                    seen_none += 1
                else:
                    assert seen_none == 0, (
                        "Tracing local_map is only currently supported with None placements last."
                    )
            return seen_none

        inputs_none_placements = check_none_last(in_placements.value)  # type: ignore[attr-defined]
        output_none_placements = check_none_last(out_placements.value)  # type: ignore[attr-defined]

        local_map_kwargs = {
            "out_placements": out_placements.value,  # type: ignore[attr-defined]
            "in_placements": in_placements.value,  # type: ignore[attr-defined]
            "redistribute_inputs": redistribute_inputs.value,  # type: ignore[attr-defined]
            "in_grad_placements": in_grad_placements.value,  # type: ignore[attr-defined]
            "device_mesh": device_mesh.value,  # type: ignore[attr-defined]
        }
        assert local_map_kwargs["device_mesh"] is not None, (
            "Not yet implemented, please manually provide a device_mesh to local_map."
        )
        mesh = local_map_kwargs["device_mesh"]

        # For Autoparallel, the initial trace is done with global shapes, then we decide model weights sharding,
        # and reuse the graph. Since the sharding decision is after the initial trace, we can't trace with local shapes.
        # For local_map however, since we specify all placements, we can trace with local shapes.

        # Step 1: Validate the annotated function matches the input_placements (i.e. that it can run in eager)
        template = (
            "Expecting {expected} {inputs_or_outputs} to local_map function based on placements"
            ", but found {actual}. Please ensure the count matches for eager. "
        )
        assert len(in_placements.value) == len(user_args), template.format(  # type: ignore[attr-defined]
            expected=len(in_placements.value),  # type: ignore[attr-defined]
            inputs_or_outputs="inputs",
            actual=len(user_args),
        )

        from torch._higher_order_ops.local_map import (
            redistribute_fw_inputs,
            redistribute_fw_outputs,
        )

        # Step 2: Convert inputs to local shapes
        priors = {}
        for placements, vt in zip(in_placements.value, user_args):  # type: ignore[attr-defined]
            if isinstance(vt, variables.lazy.LazyVariableTracker):
                vt = variables.lazy.LazyVariableTracker.realize_all(vt)

            if not vt.is_tensor():
                assert placements is None
                continue

            global_tensor = vt.as_proxy().node.meta["example_value"]
            # NOTE: We don't support local_map region relying on exact grad_fn information
            # This is okay since accessing grad_fn is a graph break.
            local_tensor = redistribute_fw_inputs(
                (global_tensor,),
                (placements,),
                mesh,
            )
            local_tensor = local_tensor[0]

            priors[vt] = global_tensor
            vt.as_proxy().node.meta["example_value"] = local_tensor
            # pyrefly: ignore [missing-attribute]
            vt.synchronize_attributes(tx)

        # Step 3: Trace local_map subgraph with local tensors
        (
            p_args,
            p_kwargs,
            example_value,
            body_r,
            body_gmod,
            body_name,
            body_graph_output_vts,
            _,
        ) = self.create_wrapped_node(
            tx, user_func, user_args, kwargs, self.value._name, subgraph_name="subgraph"
        )

        # Step 4: Validate traced graph signature still matches placement information
        expected_num_inputs = len(in_placements.value) - inputs_none_placements  # type: ignore[attr-defined]
        actual_num_inputs = len(body_gmod.graph.find_nodes(op="placeholder"))
        expected_num_outputs = len(out_placements.value) - output_none_placements  # type: ignore[attr-defined]
        assert len(body_gmod.graph.find_nodes(op="output")) == 1
        actual_num_outputs = len(body_gmod.graph.find_nodes(op="output")[0].args[0])

        template = (
            "Expecting {expected} {inputs_or_outputs} to local_map function based on placements"
            ", but found {actual}. If the count matches for eager, "
            "Dynamo may have flattened {inputs_or_outputs} to the function or found additional "
            "tensors used via closures. "
            "Please adjust the input placements to match what the traced graph sees: \n{gm_str}."
        )

        def make_error_msg(*args: Any) -> str:
            expected_num, actual_num, inputs_or_outputs = args
            gm_str = body_gmod.print_readable(print_output=False)
            return template.format(
                expected=expected_num,
                inputs_or_outputs=inputs_or_outputs,
                actual=actual_num,
                gm_str=gm_str,
            )

        if expected_num_inputs != actual_num_inputs:
            raise AssertionError(
                make_error_msg(expected_num_inputs, actual_num_inputs, "inputs")
            )
        if expected_num_outputs != actual_num_outputs:
            raise AssertionError(
                make_error_msg(expected_num_outputs, actual_num_outputs, "outputs")
            )

        if inputs_none_placements > 0:
            expected_input_nodes = [
                arg.as_proxy().node for arg in user_args[:-inputs_none_placements]
            ]
        else:
            expected_input_nodes = [arg.as_proxy().node for arg in user_args]
        actual_input_nodes = [proxy.node for proxy in p_args]
        assert actual_input_nodes[0].op == "get_attr"
        assert "subgraph" in actual_input_nodes[0].target  # type: ignore[attr-defined]
        assert len(expected_input_nodes) == len(actual_input_nodes) - 1
        for expected_order, actual_order in zip(
            expected_input_nodes, actual_input_nodes[1:]
        ):
            assert expected_order == actual_order, (
                "Dynamo changed the order of inputs to the local_map function, please adjust "
                f"the order of inputs and input_placements from {expected_input_nodes}, to: {actual_input_nodes[1:]}"
            )
        assert len(p_kwargs) == 0

        # Step 5: Install local_map subgraph
        p_kwargs = {key: value.as_proxy() for key, value in kwargs.items()}
        out = _call_function_with_auto_output_flattening(
            tx,
            self.value,
            p_args,
            p_kwargs,
            example_value,
            body_r,
            body_graph_output_vts,
        )

        # Step 6: Restore inputs and outputs to global shapes
        for vt, global_tensor in priors.items():
            vt.as_proxy().node.meta["example_value"] = global_tensor
            # pyrefly: ignore [missing-attribute]
            vt.synchronize_attributes(tx)

        outs = out.items if isinstance(out, TupleVariable) else [out]
        assert len(outs) == len(out_placements.value)  # type: ignore[attr-defined]
        for placements, vt in zip(out_placements.value, outs):  # type: ignore[attr-defined]
            if not vt.is_tensor():  # type: ignore[attr-defined]
                assert placements is None
                continue

            local_tensor = vt.as_proxy().node.meta["example_value"]  # type: ignore[attr-defined]

            # NOTE: We don't support code after the local_map region relying on exact grad_fn information
            # This is okay since accessing grad_fn is a graph break.
            global_tensor = redistribute_fw_outputs(
                (local_tensor,),
                (placements,),
                mesh,
                num_activations=0,  # this is not the joint
            )
            global_tensor = global_tensor[0]

            vt.as_proxy().node.meta["example_value"] = global_tensor  # type: ignore[attr-defined]
            vt.synchronize_attributes(tx)  # type: ignore[attr-defined]

        # TODO: Figure out how to handle output order diverging from eager

        # Treat as const, so we don't have to deal with Placement types in fx IR
        # Guarded with EQUALS_MATCH on local_map call's arguments
        body_gmod.meta["local_map_kwargs"] = {
            "out_placements": out_placements.value[:expected_num_outputs],  # type: ignore[attr-defined]
            "in_placements": in_placements.value[:expected_num_inputs],  # type: ignore[attr-defined]
            "redistribute_inputs": redistribute_inputs.value,  # type: ignore[attr-defined]
            "in_grad_placements": in_grad_placements.value,  # type: ignore[attr-defined]
            "device_mesh": device_mesh.value,  # type: ignore[attr-defined]
        }
        assert out is not None
        return out