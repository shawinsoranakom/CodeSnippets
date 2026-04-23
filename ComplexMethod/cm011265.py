def forward_one_chunk(
        self,
        fwd_chunk_id: int,
        args: tuple[Any, ...],
        kwargs: dict[str, Any] | None = None,
        save_forward_output: bool = True,
    ):
        """
        Perform forward pass on the stage with one microbatch.
        `args` and `kwargs` are the inputs from *external* to this stage.
        As of Sept 2024:
        - `args` applies to the first stage only, other stages receives args
          through activation transmission.
        - `kwargs` can be passed to all stages via respective `step` calls.
        """

        if self.is_first:
            # First stage doesn't need to receive anything
            composite_args = args
        else:
            # Receive activations for this chunk
            # Activations only come in args form
            composite_args = self._retrieve_recv_activations(fwd_chunk_id)

        composite_kwargs = kwargs or {}

        if self._runtime_validate:
            self._validate_stage_tensors(
                f"Stage {self.stage_index} forward inputs",
                self._stage_meta.inputs,
                composite_args,
            )

        # Compute forward
        try:
            output = self.forward_maybe_with_nosync(*composite_args, **composite_kwargs)

        except Exception as e:
            exc_msg = f"""
            {self.log_prefix} failed to run forward:
            args: {map_debug_info(composite_args)}
            kwargs: {map_debug_info(composite_kwargs)}
            """
            raise RuntimeError(exc_msg) from e

        # See [Note: pipeline model output type]
        output_tuple = _normalize_model_output_as_tuple(output)

        # Prepare for final output merge or reduction
        # Output chunks is only used for the last stage since we only merge the output of the last stage
        if self.is_last and save_forward_output:
            self.output_chunks.append(output)
        # Save activations and inputs for backward
        flat_args = flatten_args(composite_args)
        flat_kwargs = flatten_args(composite_kwargs)
        flatten_input_tensors = flat_args + flat_kwargs
        self.fwd_cache[fwd_chunk_id] = (
            output_tuple,  # stage_output
            flatten_input_tensors,  # input_values
        )

        logger.debug(
            "%s Forwarded chunk %s, outputs: %s",
            self.log_prefix,
            fwd_chunk_id,
            map_debug_info(output),
        )
        # Validate outputs before P2P send; skipped for last stage (outputs
        # go to loss/user, not via send/recv).
        if self._runtime_validate and not self.is_last:
            self._validate_stage_tensors(
                f"Stage {self.stage_index} forward outputs",
                self._stage_meta.outputs,
                output_tuple,
            )

        # We return the original user-provided output, not normalized to tuple.
        # See [Note: pipeline model output type]
        return output