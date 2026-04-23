def test_scaled_dot_product_attention(self, device, batch_size, input_dim, attn_mask_dim, is_causal, dropout_p):
        def sdp_ref(
                q,
                k,
                v,
                attn_mask=None,
                dropout_p=0.0):
            E = q.size(-1)
            q = q / math.sqrt(E)
            # (B, Nt, E) x (B, E, Ns) -> (B, Nt, Ns)
            if attn_mask is not None:
                attn = torch.baddbmm(attn_mask, q, k.transpose(-2, -1))
            else:
                attn = torch.bmm(q, k.transpose(-2, -1))

            attn = torch.nn.functional.softmax(attn, dim=-1)
            if dropout_p > 0.0:
                attn = torch.nn.functional.dropout(attn, p=dropout_p)
            # (B, Nt, Ns) x (B, Ns, E) -> (B, Nt, E)
            output = torch.bmm(attn, v)
            return output
        # TODO: Support cross-device / dtype testing properly when instantiate_device_type_tests() is used.
        dtypes = [torch.double, torch.float]
        for dtype in dtypes:
            N = batch_size

            def rand_tensor(*shape):
                return torch.randn(shape, device=device, dtype=dtype)

            # This test compares python and C++ implementations of SDP.
            N_prime, L, S, E = 2, 4, 3, 6
            if input_dim == 3:
                query = rand_tensor(N, L, E)
                key = rand_tensor(N, S, E)
                value = rand_tensor(N, S, E)
            elif input_dim == 4:
                query = rand_tensor(N, N_prime, L, E)
                key = rand_tensor(N, N_prime, S, E)
                value = rand_tensor(N, N_prime, S, E)
            else:
                self.fail(f'Invalid input_dim {input_dim} encountered in SDP test')

            attn_mask = None
            if attn_mask_dim is not None:
                if attn_mask_dim not in [2, input_dim]:
                    raise AssertionError(f"attn_mask_dim should be 2 or {input_dim}, got {attn_mask_dim}")
                mask_size = (L, S) if attn_mask_dim == 2 else ((N, L, S) if input_dim == 3 else (N, N_prime, L, S))
                attn_mask = (torch.ones(mask_size, device=device, dtype=torch.bool).tril() if is_causal
                             else torch.randint(0, 2, size=mask_size, device=device, dtype=torch.bool))

            with freeze_rng_state():
                # Python impl only supports float mask and 3D inputs.
                attn_mask_float = attn_mask
                if attn_mask_float is not None:
                    attn_mask_float = torch.zeros_like(attn_mask, dtype=query.dtype)
                    attn_mask_float.masked_fill_(attn_mask.logical_not(), float("-inf"))
                q, k, v = query.view(-1, L, E), key.view(-1, S, E), value.view(-1, S, E)
                a = attn_mask_float
                if a is not None and attn_mask_dim > 3:
                    a = a.view(-1, L, S)
                expected = sdp_ref(q, k, v, attn_mask=a, dropout_p=dropout_p)
                if input_dim > 3:
                    expected = expected.view(-1, N_prime, L, E)

            with freeze_rng_state():
                if is_causal:
                    # NB: Don't pass attn_mask here
                    actual = torch.nn.functional.scaled_dot_product_attention(
                        query, key, value, None, dropout_p, is_causal)

                    # Error case: both explicit attn_mask and is_causal are set
                    with self.assertRaisesRegex(RuntimeError,
                                                "Explicit attn_mask should not be set when is_causal=True"):
                        torch.nn.functional.scaled_dot_product_attention(
                            query, key, value, attn_mask, dropout_p, is_causal)
                else:
                    actual = torch.nn.functional.scaled_dot_product_attention(
                        query, key, value, attn_mask, dropout_p, is_causal)
                    # This test the fully masked out rows case
                if torch.isnan(expected).any():
                    row_sums = attn_mask.sum(dim=-1)
                    masked_out_rows = (row_sums == 0)

                    for _ in range((input_dim - attn_mask_dim) - 1):
                        masked_out_rows = masked_out_rows.unsqueeze(0)

                    masked_out_rows = masked_out_rows.expand(expected.shape[:-1])
                    # Slice out the fully masked rows from expected and actual
                    expected_masked_out = expected[masked_out_rows]
                    actual_masked_out = actual[masked_out_rows]

                    expected_all_nan = torch.isnan(expected_masked_out).all()
                    actual_all_zero = (actual_masked_out.abs().sum() == 0)

                    self.assertTrue(expected_all_nan)
                    self.assertTrue(actual_all_zero)
                    return

                self.assertEqual(actual, expected)

        if attn_mask_dim is None:
            q = q.double().clone()
            k = k.double().clone()
            v = v.double().clone()
            q.requires_grad_()
            k.requires_grad_()
            v.requires_grad_()

            if not gradcheck(lambda *args, **kwargs: wrapper_set_seed(sdp_ref, *args, **kwargs),
                             (q, k, v, attn_mask, dropout_p)):
                raise AssertionError("gradcheck failed for sdp_ref")
            if not gradcheck(lambda *args, **kwargs:
                             wrapper_set_seed(torch.nn.functional.scaled_dot_product_attention, *args, **kwargs),
                             (q, k, v, attn_mask, dropout_p)):
                raise AssertionError("gradcheck failed for scaled_dot_product_attention")

        def test_incompatible_mask(self, device):
            def ones_tensor(*shape):
                return torch.ones(shape, dtype=torch.float32)
            S, L, E, H = 1, 2, 4, 1
            qkv = ones_tensor(S, L, E)

            mha = nn.MultiheadAttention(E, H)
            mha.in_proj_weight = Parameter(torch.ones((E * 3, E)))
            mha.out_proj.weight = Parameter(torch.ones((E, E)))
            qkv = qkv.to(float)
            kpm = ones_tensor(S, L) * float("-inf")
            am = ones_tensor(L, L).to(bool)

            def func():
                return mha(qkv, qkv, qkv, need_weights=False, key_padding_mask=kpm, attn_mask=am)

            self.assertRaises(RuntimeError, func)