def generate_export(
        self,
        start_tokens,
        seq_len,
        eos_token=None,
        context=None,
        temperature=1.0,
        filter_logits_fn=None,
        filter_thres=0.9,
        **kwargs,
    ):
        was_training = self.net.training
        num_dims = len(start_tokens.shape)

        if num_dims == 1:
            start_tokens = start_tokens[None, :]

        b, t = start_tokens.shape

        self.net.eval()
        out = start_tokens
        mask = kwargs.pop("mask", None)

        if mask is None:
            mask = paddle.full_like(out, True, dtype=paddle.bool)

        i_idx = paddle.full([], 0)
        while i_idx < paddle.to_tensor(seq_len):
            x = out[:, -self.max_seq_len :]
            paddle.jit.api.set_dynamic_shape(x, [-1, -1])
            mask = mask[:, -self.max_seq_len :]
            paddle.jit.api.set_dynamic_shape(mask, [-1, -1])
            logits = self.net(x, mask=mask, context=context, seq_len=i_idx, **kwargs)[
                :, -1, :
            ]
            if filter_logits_fn in {top_k, top_p}:
                filtered_logits = filter_logits_fn(logits, thres=filter_thres)

                probs = F.softmax(filtered_logits / temperature, axis=-1)

            sample = paddle.multinomial(probs, 1)
            out = paddle.concat((out, sample), axis=-1)

            pad_mask = paddle.full(shape=[mask.shape[0], 1], fill_value=1, dtype="bool")
            mask = paddle.concat((mask, pad_mask), axis=1)
            if (
                eos_token is not None
                and (
                    paddle.cumsum((out == eos_token).cast(paddle.int64), 1)[:, -1] >= 1
                ).all()
            ):
                break
            i_idx += 1
        out = out[:, t:]
        if num_dims == 1:
            out = out.squeeze(0)
        return out