def _optimize_forward_intermediates(self):
        """
        We optimize the forward intermediates by categorize forward intermediates into categories
        and construct a ScanForwardIntermediatesHandlingPolicy for them

        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Need remove aliasing in fw_gm:\n%s",
                self.hop_partitioned_graph.fw_gm.print_readable(print_output=False),
            )

        fw_gm = self.hop_partitioned_graph.fw_gm
        fw_all_outputs = _find_hop_subgraph_outputs(fw_gm)
        phs = list(fw_gm.graph.find_nodes(op="placeholder"))
        fw_outputs = fw_all_outputs[: self.hop_partitioned_graph.n_fw_outputs]
        fw_intermediates = fw_all_outputs[self.hop_partitioned_graph.n_fw_outputs :]

        init_phs, xs_phs, additional_inputs_phs = pytree.tree_unflatten(
            phs, self.fw_spec
        )
        init_node_set, xs_node_set, addi_node_set = (
            set(init_phs),
            set(xs_phs),
            set(additional_inputs_phs),
        )

        if len(self.forward_intermediates_handling_policies) != 0:
            raise AssertionError(
                "forward_intermediates_handling_policies should be empty"
            )
        if len(self.saved_fw_xs) != 0:
            raise AssertionError("saved_fw_xs should be empty")
        if len(self.saved_fw_additional_inputs) != 0:
            raise AssertionError("saved_fw_additional_inputs should be empty")
        intermediate_idx_to_ph_idx = {}
        ph_idx = {ph: i for i, ph in enumerate(phs)}
        for i, out in enumerate(fw_intermediates):
            if out in init_node_set:
                self.forward_intermediates_handling_policies.append(
                    ScanForwardIntermediatesHandlingPolicy.CLONE
                )
                intermediate_idx_to_ph_idx[i] = ph_idx[out]
            elif out in xs_node_set:
                self.forward_intermediates_handling_policies.append(
                    ScanForwardIntermediatesHandlingPolicy.REMOVE_XS
                )
                intermediate_idx_to_ph_idx[i] = ph_idx[out]
            elif out in addi_node_set:
                self.forward_intermediates_handling_policies.append(
                    ScanForwardIntermediatesHandlingPolicy.REMOVE_ADDITIONAL_INPUTS
                )
                intermediate_idx_to_ph_idx[i] = ph_idx[out]
            else:
                self.forward_intermediates_handling_policies.append(
                    ScanForwardIntermediatesHandlingPolicy.KEEP
                )

        new_output_node = []
        real_graph_inputs = (
            list(self.init) + list(self.xs) + list(self.additional_inputs)
        )
        fw_output_node = next(iter(fw_gm.graph.find_nodes(op="output")))
        for intermediate_idx, (node, policy) in enumerate(
            zip(fw_intermediates, self.forward_intermediates_handling_policies)
        ):
            if policy == ScanForwardIntermediatesHandlingPolicy.CLONE:
                new_output_node.append(self._insert_clone(node, fw_output_node))
            elif policy == ScanForwardIntermediatesHandlingPolicy.REMOVE_XS:
                if intermediate_idx not in intermediate_idx_to_ph_idx:
                    raise AssertionError(
                        f"intermediate_idx {intermediate_idx} not in intermediate_idx_to_ph_idx"
                    )
                inp_idx = intermediate_idx_to_ph_idx[intermediate_idx]
                self.saved_fw_xs.append(real_graph_inputs[inp_idx])
            elif (
                policy
                == ScanForwardIntermediatesHandlingPolicy.REMOVE_ADDITIONAL_INPUTS
            ):
                if intermediate_idx not in intermediate_idx_to_ph_idx:
                    raise AssertionError(
                        f"intermediate_idx {intermediate_idx} not in intermediate_idx_to_ph_idx for REMOVE_ADDITIONAL_INPUTS"
                    )
                inp_idx = intermediate_idx_to_ph_idx[intermediate_idx]
                self.saved_fw_additional_inputs.append(real_graph_inputs[inp_idx])
            else:
                new_output_node.append(node)

        fw_output_node.args = (tuple(fw_outputs) + tuple(new_output_node),)
        fw_gm.graph.lint()
        fw_gm.recompile()

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "after removing aliasing:\n%s", fw_gm.print_readable(print_output=False)
            )