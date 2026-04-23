def generate(
        self,
        start_tokens,
        seq_len,
        eos_token=None,
        temperature=1.0,
        filter_logits_fn=top_k,
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

        for _ in range(seq_len):
            x = out[:, -self.max_seq_len :]
            mask = mask[:, -self.max_seq_len :]
            logits = self.net(x, mask=mask, **kwargs)[:, -1, :]
            if filter_logits_fn in {top_k, top_p}:
                filtered_logits = filter_logits_fn(logits, thres=filter_thres)

                probs = F.softmax(filtered_logits / temperature, axis=-1)
            else:
                raise NotImplementedError("The filter_logits_fn is not supported ")

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
        out = out[:, t:]
        if num_dims == 1:
            out = out.squeeze(0)
        return out