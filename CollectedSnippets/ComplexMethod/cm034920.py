def _prepare_qkv(self, queries, keys, values, cache=None):
        if keys is None:  # self-attention
            keys, values = queries, queries
            static_kv = False
        else:  # cross-attention
            static_kv = True

        q = self.q_fc(queries)
        q = paddle.reshape(x=q, shape=[0, 0, self.n_head, self.d_key])
        q = paddle.transpose(x=q, perm=[0, 2, 1, 3])

        if cache is not None and static_kv and "static_k" in cache:
            # for encoder-decoder attention in inference and has cached
            k = cache["static_k"]
            v = cache["static_v"]
        else:
            k = self.k_fc(keys)
            v = self.v_fc(values)
            k = paddle.reshape(x=k, shape=[0, 0, self.n_head, self.d_key])
            k = paddle.transpose(x=k, perm=[0, 2, 1, 3])
            v = paddle.reshape(x=v, shape=[0, 0, self.n_head, self.d_value])
            v = paddle.transpose(x=v, perm=[0, 2, 1, 3])

        if cache is not None:
            if static_kv and not "static_k" in cache:
                # for encoder-decoder attention in inference and has not cached
                cache["static_k"], cache["static_v"] = k, v
            elif not static_kv:
                # for decoder self-attention in inference
                cache_k, cache_v = cache["k"], cache["v"]
                k = paddle.concat([cache_k, k], axis=2)
                v = paddle.concat([cache_v, v], axis=2)
                cache["k"], cache["v"] = k, v

        return q, k, v