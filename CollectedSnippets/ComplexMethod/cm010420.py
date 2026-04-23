def _check_partition_boundary(self) -> None:
        """check partitioned graph is in valid state."""
        invalid_reasons = []
        fw_outputs = _find_hop_subgraph_outputs(self.fw_gm)
        for i, out in enumerate(fw_outputs):
            if "val" not in out.meta:
                invalid_reasons.append(f"fw_gm output[{i}] doesn't have a 'val' meta.")
            elif not isinstance(out.meta["val"], (torch.SymInt, torch.Tensor)):
                invalid_reasons.append(
                    f"fw_gm output[{i}] is of type {type(out.meta['val'])} but only SymInt or Tensor are allowed."
                )

            elif (
                isinstance(out.meta["val"], torch.SymInt)
                and is_complex_expr(out.meta["val"].node.expr)
                and self.no_complex_exprs_at_boundary
            ):
                invalid_reasons.append(
                    f"fw_gm output[{i}] must be of type SymInt with basic symbols or "
                    f"Tensor but got {type(out.meta['val'])} {out.meta['val']}"
                )

        if len(fw_outputs) != self.n_fw_outputs + self.n_intermediates:
            invalid_reasons.append(
                f"len(fw_outputs) ({len(fw_outputs)}) != n_fw_outputs ({self.n_fw_outputs}) + n_intermediates ({self.n_intermediates})"
            )

        bw_phs = list(self.bw_gm.graph.find_nodes(op="placeholder"))

        if len(fw_outputs) != len(bw_phs):
            invalid_reasons.append(
                f"Expect number of fw_gm's output to be the same as bw_gm's input but "
                f"fw_gm has {len(fw_outputs)} outputs, bw_gm takes {len(bw_phs)} inputs."
            )

        original_forward_outputs = fw_outputs[: self.n_fw_outputs]
        fw_intermediates = fw_outputs[self.n_fw_outputs :]

        bw_intermediates = bw_phs[: -self.n_fw_outputs]
        bw_grads = bw_phs[-self.n_fw_outputs :]

        def _match_size_or_expr(
            val1: torch.SymInt | torch.Tensor,
            val2: torch.SymInt | torch.Tensor,
        ) -> bool:
            if type(val1) is not type(val2):
                return False

            if isinstance(val1, torch.SymInt) and isinstance(val2, torch.SymInt):
                return val1.node.expr == val2.node.expr
            elif isinstance(val1, torch.Tensor) and isinstance(val2, torch.Tensor):
                return val1.size() == val2.size()

            return False

        for fw, bw in zip(fw_intermediates, bw_intermediates):
            if fw.name != bw.name or not _match_size_or_expr(
                fw.meta["val"], bw.meta["val"]
            ):
                invalid_reasons.append("fw intermediates don't match bw intermediates")

        for fw_out, bw_grad in zip(original_forward_outputs, bw_grads):
            if not _match_size_or_expr(fw_out.meta["val"], bw_grad.meta["val"]):
                invalid_reasons.append("fw outputs don't match bw gradients")

        if len(invalid_reasons) > 0:
            newline = "\n"
            raise RuntimeError(
                f"Invalid HopPartitionedGraph. Reasons:\n{newline.join(invalid_reasons)}"
            )