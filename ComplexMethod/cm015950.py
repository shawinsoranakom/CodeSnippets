def _multihead_attn_test_helper(
            add_key_padding_mask=False,
            add_bias_kv=False,
            add_zero_attn=False,
            saved_kv=False,
            same_embed_dim=False,
            average_attn_weights=average_attn_weights,
        ):
            for _ in range(100):
                batch_sz, seq_len = (random.randint(2, 10) for r in range(2))
                d_head = random.randint(3, 10)
                nheads = random.randint(2, 5) * 2
                d_model = d_head * nheads
                if same_embed_dim:
                    kv_dim = d_model
                else:
                    kv_dim = random.randint(5, 20)
                dims = [batch_sz, seq_len, kv_dim]

                saved_k = None
                saved_k_tensor = None
                saved_v = None
                saved_v_tensor = None
                if saved_kv:
                    saved_k = np.random.rand(batch_sz * nheads, seq_len, d_head)
                    saved_k_tensor = torch.from_numpy(saved_k).to(
                        torch.get_default_dtype()
                    )
                    saved_v = np.random.rand(batch_sz * nheads, seq_len, d_head)
                    saved_v_tensor = torch.from_numpy(saved_v).to(
                        torch.get_default_dtype()
                    )

                key_padding_mask = None
                key_padding_mask_tensor = None
                if add_key_padding_mask:
                    seq_mask = np.random.randint(0, 2, (1, seq_len))
                    key_padding_mask = np.repeat(seq_mask, batch_sz, axis=0) == 1
                    key_padding_mask_tensor = torch.from_numpy(key_padding_mask)
                decoder_state = np.random.rand(batch_sz, d_model)
                K = np.random.rand(*dims)
                V = K
                Q = np.expand_dims(decoder_state, 1)
                attn_mask = np.random.randint(0, 2, size=(1, seq_len))
                attn_mask_tensor = torch.from_numpy(attn_mask).float()
                attn_mask_tensor.masked_fill_(attn_mask_tensor == 0, float("-inf"))
                attn_mask_tensor.masked_fill_(attn_mask_tensor > 0, float("0.0"))

                decoder_state_tensor = torch.from_numpy(decoder_state).to(
                    torch.get_default_dtype()
                )
                source_hid_tensor = (
                    torch.from_numpy(K).to(torch.get_default_dtype()).transpose(0, 1)
                )

                multihead_attn_module = MultiheadAttention(
                    d_model,
                    nheads,
                    add_bias_kv=add_bias_kv,
                    add_zero_attn=add_zero_attn,
                    kdim=kv_dim,
                    vdim=kv_dim,
                )

                if add_bias_kv:
                    bias_k = multihead_attn_module.bias_k.detach().numpy()
                    bias_v = multihead_attn_module.bias_v.detach().numpy()
                else:
                    bias_k = None
                    bias_v = None

                _Q = decoder_state_tensor.unsqueeze(1).transpose(0, 1)
                _V = source_hid_tensor
                _K = source_hid_tensor

                if multihead_attn_module._qkv_same_embed_dim:
                    (
                        result,
                        result_weight,
                    ) = torch.nn.functional.multi_head_attention_forward(
                        _Q,
                        _K,
                        _V,
                        d_model,
                        nheads,
                        multihead_attn_module.in_proj_weight,
                        multihead_attn_module.in_proj_bias,
                        multihead_attn_module.bias_k,
                        multihead_attn_module.bias_v,
                        multihead_attn_module.add_zero_attn,
                        multihead_attn_module.dropout,
                        multihead_attn_module.out_proj.weight,
                        multihead_attn_module.out_proj.bias,
                        multihead_attn_module.training,
                        key_padding_mask_tensor,
                        True,
                        attn_mask_tensor,
                        static_k=saved_k_tensor,
                        static_v=saved_v_tensor,
                        average_attn_weights=average_attn_weights,
                        is_causal=False,
                    )
                else:
                    (
                        result,
                        result_weight,
                    ) = torch.nn.functional.multi_head_attention_forward(
                        _Q,
                        _K,
                        _V,
                        d_model,
                        nheads,
                        None,
                        multihead_attn_module.in_proj_bias,
                        multihead_attn_module.bias_k,
                        multihead_attn_module.bias_v,
                        multihead_attn_module.add_zero_attn,
                        multihead_attn_module.dropout,
                        multihead_attn_module.out_proj.weight,
                        multihead_attn_module.out_proj.bias,
                        multihead_attn_module.training,
                        key_padding_mask_tensor,
                        True,
                        attn_mask_tensor,
                        True,
                        multihead_attn_module.q_proj_weight,
                        multihead_attn_module.k_proj_weight,
                        multihead_attn_module.v_proj_weight,
                        static_k=saved_k_tensor,
                        static_v=saved_v_tensor,
                        average_attn_weights=average_attn_weights,
                        is_causal=False,
                    )

                result = result.squeeze(0).detach().numpy()

                if multihead_attn_module._qkv_same_embed_dim:
                    q_proj_weight = multihead_attn_module.in_proj_weight[:d_model]
                    k_proj_weight = multihead_attn_module.in_proj_weight[
                        d_model : (d_model * 2)
                    ]
                    v_proj_weight = multihead_attn_module.in_proj_weight[
                        (d_model * 2) :
                    ]
                else:
                    q_proj_weight = multihead_attn_module.q_proj_weight
                    k_proj_weight = multihead_attn_module.k_proj_weight
                    v_proj_weight = multihead_attn_module.v_proj_weight

                Q_fc = _fc(
                    Q, q_proj_weight, multihead_attn_module.in_proj_bias[:d_model]
                )
                K_fc = _fc(
                    K,
                    k_proj_weight,
                    multihead_attn_module.in_proj_bias[d_model : (d_model * 2)],
                )
                V_fc = _fc(
                    V,
                    v_proj_weight,
                    multihead_attn_module.in_proj_bias[(d_model * 2) :],
                )

                if add_bias_kv:
                    K_fc = np.concatenate(
                        (K_fc, np.repeat(bias_k, K_fc.shape[0], axis=0)), axis=1
                    )
                    V_fc = np.concatenate(
                        (V_fc, np.repeat(bias_v, V_fc.shape[0], axis=0)), axis=1
                    )
                    if attn_mask is not None:
                        attn_mask = np.concatenate((attn_mask, np.ones([1, 1])), axis=1)
                    if key_padding_mask is not None:
                        key_padding_mask = np.concatenate(
                            (
                                key_padding_mask,
                                np.full((batch_sz, 1), False, dtype=bool),
                            ),
                            axis=1,
                        )
                    dims[1] += 1
                Q_split = _split_heads_ref(Q_fc, [batch_sz, 1, d_model], nheads, d_head)

                if saved_k is not None:
                    K_split = np.reshape(saved_k, [dims[0], nheads, dims[1], d_head])
                else:
                    K_split = _split_heads_ref(K_fc, dims, nheads, d_head)

                if saved_v is not None:
                    V_split = np.reshape(saved_v, [dims[0], nheads, dims[1], d_head])
                else:
                    V_split = _split_heads_ref(V_fc, dims, nheads, d_head)

                if add_zero_attn:
                    dims[1] += 1
                    K_split = np.concatenate(
                        (
                            K_split,
                            np.zeros(
                                [
                                    K_split.shape[0],
                                    K_split.shape[1],
                                    1,
                                    K_split.shape[3],
                                ]
                            ),
                        ),
                        axis=2,
                    )
                    V_split = np.concatenate(
                        (
                            V_split,
                            np.zeros(
                                [
                                    V_split.shape[0],
                                    V_split.shape[1],
                                    1,
                                    V_split.shape[3],
                                ]
                            ),
                        ),
                        axis=2,
                    )

                    if attn_mask is not None:
                        attn_mask = np.concatenate((attn_mask, np.ones([1, 1])), axis=1)

                    if key_padding_mask is not None:
                        key_padding_mask = np.concatenate(
                            (
                                key_padding_mask,
                                np.full((batch_sz, 1), False, dtype=bool),
                            ),
                            axis=1,
                        )
                attn_heads, ref_attn_weight = _scaled_dot_attn_ref(
                    Q=Q_split,
                    K=K_split,
                    V=V_split,
                    dims=Q_split.shape,
                    unseen_mask=attn_mask,
                    key_padding_mask=key_padding_mask,
                )
                combined_attn_heads = _combine_heads_ref(
                    X=attn_heads, dims=[batch_sz, 1], nheads=nheads, d_head=d_head
                )

                reference = _fc(
                    combined_attn_heads,
                    multihead_attn_module.out_proj.weight,
                    multihead_attn_module.out_proj.bias,
                )
                reference = np.squeeze(reference, axis=1)

                # result = reference
                self.assertEqual(tuple(result.shape), (batch_sz, d_model))
                np.testing.assert_allclose(result, reference, atol=1e-5)

                # result_weight = ref_attn_weight
                result_weight = result_weight.detach().numpy()
                self.assertEqual(
                    tuple(result_weight.shape), tuple(ref_attn_weight.shape)
                )
                np.testing.assert_allclose(result_weight, ref_attn_weight, atol=1e-5)