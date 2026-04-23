def _int4_call(self, inputs, reverse=False):
        if not reverse:
            return super()._int4_call(inputs)
        else:
            block_size = getattr(self, "_int4_block_size", None)

            if self.tie_weights:
                embeddings = ops.transpose(self._embeddings)
                scale = self.embeddings_scale
                # For tied weights, scale shape is (input_dim,) or
                # (input_dim, n_groups). For per-channel, transpose scale.
                if block_size is None or block_size == -1:
                    scale = ops.transpose(scale)
            else:
                embeddings = self.reverse_embeddings
                scale = self.reverse_embeddings_scale

            unpacked_embeddings = quantizers.unpack_int4(
                embeddings, self.output_dim, axis=0
            )

            if self.inputs_quantizer:
                inputs, inputs_scale = self.inputs_quantizer(inputs)
            else:
                inputs_scale = ops.ones((1,), dtype=self.compute_dtype)

            if block_size is None or block_size == -1:
                # Per-channel: do matmul then dequantize
                logits = ops.matmul(inputs, unpacked_embeddings)
                logits = ops.cast(logits, self.compute_dtype)
                logits = ops.divide(logits, ops.multiply(inputs_scale, scale))
            elif self.tie_weights:
                # Sub-channel with asymmetric quantization (tied weights)
                # Must dequantize embeddings before matmul for correctness
                # unpacked_embeddings shape: (output_dim, input_dim)
                # scale shape: (input_dim, n_groups)
                # embeddings_zero shape: (input_dim, n_groups)
                # g_idx shape: (output_dim,)

                # Transpose scale/zero for dequantization:
                # [input_dim, n_groups] -> [n_groups, input_dim]
                scale_t = ops.transpose(scale)
                zero_t = ops.transpose(self.embeddings_zero)

                float_embeddings = dequantize_with_sz_map(
                    ops.cast(unpacked_embeddings, self.compute_dtype),
                    scale_t,
                    zero_t,
                    self.g_idx,
                    group_axis=0,
                )

                # inputs shape: (batch, output_dim)
                # float_embeddings shape: (output_dim, input_dim)
                logits = ops.matmul(inputs, float_embeddings)
                logits = ops.divide(logits, inputs_scale)
            else:
                # Untied weights with asymmetric grouped quantization
                # Must dequantize embeddings before matmul for correctness
                # unpacked_embeddings shape: (output_dim, input_dim)
                # scale shape: (n_groups, input_dim)
                # reverse_embeddings_zero shape: (n_groups, input_dim)
                # g_idx shape: (output_dim,) - reuse from forward pass

                float_embeddings = dequantize_with_sz_map(
                    ops.cast(unpacked_embeddings, self.compute_dtype),
                    scale,
                    self.reverse_embeddings_zero,
                    self.g_idx,
                    group_axis=0,
                )

                # inputs shape: (batch, output_dim)
                # float_embeddings shape: (output_dim, input_dim)
                logits = ops.matmul(inputs, float_embeddings)
                logits = ops.divide(logits, inputs_scale)

            # Optionally soft-cap logits.
            if self.logit_soft_cap is not None:
                soft_cap = self.logit_soft_cap
                logits = ops.multiply(
                    ops.tanh(ops.divide(logits, soft_cap)), soft_cap
                )
            return logits