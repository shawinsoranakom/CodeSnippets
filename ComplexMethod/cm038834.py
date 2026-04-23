def _apply_async_impl(
        self, x: torch.Tensor, bias: torch.Tensor | None = None
    ) -> torch.Tensor:
        """
        Forward pass with base linear and LoRA on separate CUDA streams
        for overlap, using maybe_execute_in_parallel.
        Base layer runs on default stream; LoRA runs on aux stream.
        """
        assert envs.VLLM_LORA_ENABLE_DUAL_STREAM
        assert x.ndim in (2, 3)
        num_tokens = x.size(0) if x.ndim == 2 else x.size(1)
        output_size = sum(self.output_slices)

        def base_fn() -> torch.Tensor:
            return self.base_layer.quant_method.apply(self.base_layer, x, bias)

        def lora_fn() -> torch.Tensor:
            # Must be zeros, not empty: _lora_expand_kernel exits early (without
            # writing) when lora_id == -1 (no active LoRA). If uninitialized,
            # output.add_(lora_result) below would corrupt the base output.
            lora_output = torch.zeros(
                (num_tokens, output_size),
                device=self.device,
                dtype=x.dtype,
            )

            # Flatten the batch dimension for the transformers backend
            # (which uses shape (1, seq_len, hidden)), matching _apply_sync.
            x_2d = x.flatten(0, 1) if x.ndim == 3 else x
            self.punica_wrapper.add_lora_linear(
                lora_output,
                x_2d,
                self.lora_a_stacked,
                self.lora_b_stacked,
                1.0,
                self.output_slices,
                add_inputs=False,
            )
            return lora_output

        output, lora_result = maybe_execute_in_parallel(
            base_fn,
            lora_fn,
            self._events[0],
            self._events[1],
            self._lora_stream,
        )

        original_shape = output.shape if output.ndim == 3 else None

        # In transformers backend, x and output have extra batch dimension like
        # (1, seq_len, hidden_dim), while punica expects (seq_len, hidden_dim),
        # therefore we need to flatten the batch dimensions.
        if x.ndim == 3 and output.ndim == 3:
            output = output.flatten(0, 1)
            x = x.flatten(0, 1)

        output.add_(lora_result)

        # Reshape the flattened output back to its original shape,
        # as some MM encoders cannot handle flattened inputs.
        if original_shape is not None:
            output = output.reshape(original_shape)

        return output