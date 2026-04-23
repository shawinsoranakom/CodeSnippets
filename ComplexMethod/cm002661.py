def _ignore_causal_mask_sdpa(
        attention_mask: torch.Tensor | None,
        inputs_embeds: torch.Tensor,
        past_key_values_length: int,
        sliding_window: int | None = None,
        is_training: bool = False,
    ) -> bool:
        """
        Detects whether the optional user-specified attention_mask & the automatically created causal mask can be
        ignored in case PyTorch's SDPA is used, rather relying on SDPA's `is_causal` argument.

        In case no token is masked in the `attention_mask` argument, if `query_length == 1` or
        `key_value_length == query_length`, we rather rely on SDPA `is_causal` argument to use causal/non-causal masks,
        allowing to dispatch to the flash attention kernel (that can otherwise not be used if a custom `attn_mask` is
        passed).
        """
        warnings.warn(DEPRECATION_MESSAGE, FutureWarning)

        _, query_length = inputs_embeds.shape[0], inputs_embeds.shape[1]
        key_value_length = query_length + past_key_values_length

        is_tracing_ = is_tracing(inputs_embeds)

        ignore_causal_mask = False

        if attention_mask is None:
            # TODO: When tracing with TorchDynamo with fullgraph=True, the model is recompiled depending on the input
            # shape, thus SDPA's `is_causal` argument is rightfully updated
            # (see https://gist.github.com/fxmarty/1313f39037fc1c112508989628c57363). However, when using
            # `torch.export` or `torch.onnx.dynamo_export`, we must pass an example input, and `is_causal` behavior is
            # hard-coded. If a user exports a model with q_len > 1, the exported model will hard-code `is_causal=True`
            # which is in general wrong (see https://github.com/pytorch/pytorch/issues/108108).
            # Thus, we only set `ignore_causal_mask = True` if the model is set to training.
            #
            # Besides, jit.trace can not handle the `q_len > 1` condition for `is_causal`
            # ("TypeError: scaled_dot_product_attention(): argument 'is_causal' must be bool, not Tensor").
            if (
                (is_training or not is_tracing_)
                and (query_length == 1 or key_value_length == query_length)
                and (sliding_window is None or key_value_length < sliding_window)
            ):
                ignore_causal_mask = True
        elif sliding_window is None or key_value_length < sliding_window:
            if len(attention_mask.shape) == 4:
                return False
            elif not is_tracing_ and torch.all(attention_mask == 1):
                if query_length == 1 or key_value_length == query_length:
                    # For query_length == 1, causal attention and bi-directional attention are the same.
                    ignore_causal_mask = True

                # Unfortunately, for query_length > 1 and key_value_length != query_length, we cannot generally ignore
                # the attention mask, as SDPA causal mask generation may be wrong. We will set `is_causal=False` in
                # SDPA and rely on Transformers attention_mask instead, hence not setting it to None here.
                # Reference: https://github.com/pytorch/pytorch/issues/108108
                # TODO: maybe revisit this with https://github.com/pytorch/pytorch/pull/114823 in PyTorch 2.3.

        return ignore_causal_mask