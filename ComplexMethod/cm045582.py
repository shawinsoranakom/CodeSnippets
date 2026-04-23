def __call__(
        self,
        query: jax.Array,
        key: Optional[jax.Array],
        value: Optional[jax.Array],
        mask: Optional[jax.Array] = None,
        kv_memory: Optional[KVMemory] = None,
        mesh: Any = None,
    ) -> MHAOutput:
        # In shape hints below, we suppress the leading dims [...] for brevity.
        # Hence e.g. [A, B] should be read in every case as [..., A, B].
        sequence_length = query.shape[1]
        projection = self._linear_projection
        use_memory = False
        if kv_memory is not None:
            if kv_memory.k is None:
                assert kv_memory.v is None
                assert key is not None
                assert value is not None
            else:
                assert kv_memory.v is not None
                use_memory = True
        else:
            assert key is not None
            assert value is not None

        # Check that the keys and values have consistent batch size and sequence length.
        if not use_memory:
            assert key.shape[:2] == value.shape[:2], f"key/value shape: {key.shape}/{value.shape}"

        if mask is not None:
            assert mask.ndim == 4
            assert mask.shape[0] in {
                1,
                query.shape[0],
            }, f"mask/query shape: {mask.shape}/{query.shape}"
            if not use_memory:
                assert key.shape[0] in {
                    1,
                    query.shape[0],
                }, f"key/query shape: {key.shape}/{query.shape}"
            assert mask.shape[1] == 1
            assert mask.shape[2] in {
                1,
                query.shape[1],
            }, f"mask/query shape: {mask.shape}/{query.shape}"
            if not use_memory:
                assert mask.shape[3] in {
                    1,
                    key.shape[1],
                }, f"mask/query shape: {mask.shape}/{key.shape}"

        # Compute key/query/values (overload K/Q/V to denote the respective sizes).
        assert self.num_q_heads % self.num_kv_heads == 0
        query_heads = projection(
            query,
            self.key_size,
            self.num_q_heads,
            name="query",
            sharding=P("data", "model"),
            mesh=mesh,
        )  # [B, T', H, Q=K]

        new_memory = None
        key_heads = projection(
            key,
            self.key_size,
            self.num_kv_heads,
            name="key",
            sharding=P("data", "model"),
            mesh=mesh,
        )  # [B, T, H, K]
        value_heads = projection(
            value,
            self.value_size,
            self.num_kv_heads,
            name="value",
            sharding=P("data", "model"),
            mesh=mesh,
        )  # [B, T, H, V]

        rotate = RotaryEmbedding(dim=self.key_size, base_exponent=int(1e4))
        key_heads = rotate(key_heads, seq_dim=1, offset=(kv_memory.step if kv_memory else 0))
        query_heads = rotate(query_heads, seq_dim=1, offset=(kv_memory.step if kv_memory else 0))

        @functools.partial(jax.vmap)
        def update_into(mem, start, update):
            return jax.lax.dynamic_update_slice_in_dim(mem, update, start, axis=0)

        if kv_memory:
            if mesh is not None:

                @functools.partial(
                    shard_map,
                    mesh=mesh,
                    in_specs=(
                        P("data", None, "model"),
                        P("data"),
                        P("data", None, "model"),
                    ),
                    out_specs=P("data", None, "model"),
                    check_rep=False,
                )
                def update_into_shmap(mems, starts, updates):
                    return update_into(mems, starts, updates)

                key_heads = update_into_shmap(kv_memory.k, kv_memory.step, key_heads)
                value_heads = update_into_shmap(kv_memory.v, kv_memory.step, value_heads)
            else:
                key_heads = update_into(kv_memory.k, kv_memory.step, key_heads)
                value_heads = update_into(kv_memory.v, kv_memory.step, value_heads)

            new_step = kv_memory.step + sequence_length
            memory_mask = jnp.arange(kv_memory.k.shape[1]) < new_step[:, None]
            memory_mask = memory_mask[:, None, None, :]  # [B, H, T, T]
            if mask is not None:
                mask = memory_mask * mask
            else:
                mask = memory_mask

            new_memory = KVMemory(
                k=key_heads,
                v=value_heads,
                step=new_step,
            )
        # Add separate dimension for grouped query heads.
        query_heads = with_sharding_constraint(query_heads, P(self.data_axis, None, "model", None))
        key_heads = with_sharding_constraint(key_heads, P(self.data_axis, None, "model", None))
        value_heads = with_sharding_constraint(value_heads, P(self.data_axis, None, "model", None))
        b, t, h, d = query_heads.shape
        _, _, kv_h, _ = key_heads.shape
        assert h % kv_h == 0, f"query_heads {h} must be a multiple of kv_heads {kv_h}"

        query_heads = jnp.reshape(query_heads, (b, t, kv_h, h // kv_h, d))
        query_heads = with_sharding_constraint(
            query_heads, P(self.data_axis, None, "model", None, None)
        )

        # Compute attention weights.
        # Attention softmax is always carried out in fp32.
        attn_logits = jnp.einsum("...thHd,...Thd->...hHtT", query_heads, key_heads).astype(
            jnp.float32
        )
        attn_logits *= self.attn_output_multiplier
        max_attn_val = jnp.array(30.0, dtype=attn_logits.dtype)
        attn_logits = max_attn_val * jnp.tanh(attn_logits / max_attn_val)

        mask = mask[:, :, None, :, :]

        if mask is not None:
            if mask.ndim != attn_logits.ndim:
                raise ValueError(
                    f"Mask dimensionality {mask.ndim} must match logits dimensionality "
                    f"{attn_logits.ndim} for {mask.shape}/{attn_logits.shape}."
                )
            attn_logits = jnp.where(mask, attn_logits, -1e30)
        attn_weights = jax.nn.softmax(attn_logits).astype(query.dtype)  # [H, T', T]

        # Weight the values by the attention and flatten the head vectors.
        attn = jnp.einsum("...hHtT,...Thd->...thHd", attn_weights, value_heads)
        attn = with_sharding_constraint(attn, P(self.data_axis, None, "model", None, None))
        leading_dims = attn.shape[:2]
        attn = jnp.reshape(attn, (*leading_dims, -1))  # [T', H*V]
        attn = with_sharding_constraint(attn, P(self.data_axis, None, "model"))
        # Apply another projection to get the final embeddings.
        final_projection = Linear(
            self.model_size,
            with_bias=False,
            sharding=P("model", "data"),
            mesh=mesh,
        )
        return MHAOutput(final_projection(attn), new_memory)