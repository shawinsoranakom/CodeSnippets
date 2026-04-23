def _create_act_send_info(self):
        """
        Create a dict of send info for activations and output metadata.

        Output metadata is created directly with correct ``requires_grad``
        (``torch.export`` traces under ``no_grad()``, so traced values
        always have ``requires_grad=False``; at runtime, stage outputs
        carry ``requires_grad=True`` when training).
        """
        # Output index: List of receiver ranks
        act_send_info: dict[int, list] = {}
        out_idx = 0

        for user in self.node.users:
            if user.target is operator.getitem:
                gi_dsts = act_send_info.setdefault(out_idx, [])
                for gi_user in user.users:
                    dst_rank = self.find_dst_rank(gi_user)
                    if dst_rank is not None:
                        gi_dsts.append(dst_rank)
                out_idx += 1
            else:
                dsts = act_send_info.setdefault(out_idx, [])
                dst_rank = self.find_dst_rank(user)
                if dst_rank is not None:
                    dsts.append(dst_rank)

        output_node = self._get_output_node()
        output_vals: tuple[torch.Tensor] = tuple(
            v.meta["val"] for v in flatten_args(output_node.args)
        )
        # Reject DTensors and create output metadata directly with
        # correct requires_grad.
        output_metas: list[_TensorMeta] = []
        for i, val in enumerate(output_vals):
            if isinstance(val, DTensor):
                raise PipeliningMetadataError(
                    f"{self.log_prefix} DTensor detected in traced pipeline output index {i}. "
                    f"DTensor metadata propagation is NOT supported for the traced frontend "
                    f"(_PipelineStage). Use the manual PipelineStage frontend for full DTensor support."
                )
            output_metas.append(
                _TensorMeta(
                    shape=val.shape,
                    stride=val.stride(),
                    dtype=val.dtype,
                    requires_grad=self.has_backward,
                )
            )
        self._stage_meta.outputs = tuple(output_metas)

        logger.debug("%s Send info: %s", self.log_prefix, act_send_info)
        return act_send_info