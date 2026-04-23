def test_block_table_kv_cache(
        self, device, dtype, page_size, compile, actual_kv_lens, backend
    ):
        if backend == "fa2" and page_size % 256 != 0:
            self.skipTest("FA2 paged KV requires page_size divisible by 256")

        torch.manual_seed(42)

        batch_size = 4
        num_heads = 8
        head_dim = 64
        max_kv = max(actual_kv_lens)
        max_pages_per_seq = (max_kv + page_size - 1) // page_size
        cache_size = max_pages_per_seq * page_size
        total_pages = batch_size * max_pages_per_seq

        q_seqs = [
            torch.randn(1, num_heads, head_dim, device=device, dtype=dtype)
            for _ in range(batch_size)
        ]
        q_packed, cu_seq_q, max_q = pack_sequences(q_seqs, device)

        k_pages = torch.randn(
            total_pages, page_size, num_heads, head_dim, device=device, dtype=dtype
        )
        v_pages = torch.randn(
            total_pages, page_size, num_heads, head_dim, device=device, dtype=dtype
        )
        block_table = torch.randperm(
            total_pages, device=device, dtype=torch.int32
        ).view(batch_size, max_pages_per_seq)
        seqused_k = torch.tensor(actual_kv_lens, device=device, dtype=torch.int32)

        idx = (
            block_table.long()
            .view(-1, 1, 1, 1)
            .expand(-1, page_size, num_heads, head_dim)
        )
        k_gathered = k_pages.gather(0, idx).view(
            batch_size, cache_size, num_heads, head_dim
        )
        v_gathered = v_pages.gather(0, idx).view(
            batch_size, cache_size, num_heads, head_dim
        )
        k_seqs = [k_gathered[i, : actual_kv_lens[i]] for i in range(batch_size)]
        v_seqs = [v_gathered[i, : actual_kv_lens[i]] for i in range(batch_size)]

        k_real_packed, cu_seq_k_real, max_k_real = pack_sequences(k_seqs, device)
        v_real_packed = torch.cat(v_seqs, dim=0)

        attn_fn = torch.compile(varlen_attn, fullgraph=True) if compile else varlen_attn

        # Reference: no block_table
        with _use_backend(backend), torch.no_grad():
            output_reference = varlen_attn(
                q_packed,
                k_real_packed,
                v_real_packed,
                cu_seq_q,
                cu_seq_k_real,
                max_q,
                max_k_real,
            )

        cu_seq_k = torch.arange(
            0,
            (batch_size + 1) * cache_size,
            cache_size,
            device=device,
            dtype=torch.int32,
        )

        # FA2 requires cu_seq_k for paged KV; FA3/FA4 pass None
        cu_seq_k_paged = cu_seq_k if backend == "fa2" else None

        with _use_backend(backend), torch.no_grad():
            output_paged = attn_fn(
                q_packed,
                k_pages,
                v_pages,
                cu_seq_q,
                cu_seq_k_paged,
                max_q,
                cache_size,
                seqused_k=seqused_k,
                block_table=block_table,
            )

        self.assertEqual(output_paged, output_reference)

        # varlen_attn_out with paged KV cache should match
        with _use_backend(backend), torch.no_grad():
            out_buf = torch.empty_like(q_packed)
            output_out = varlen_attn_out(
                out_buf,
                q_packed,
                k_pages,
                v_pages,
                cu_seq_q,
                cu_seq_k_paged,
                max_q,
                cache_size,
                seqused_k=seqused_k,
                block_table=block_table,
            )
            self.assertEqual(output_out.data_ptr(), out_buf.data_ptr())
            self.assertEqual(out_buf, output_paged)

        # compile the lower level aten op (FA3 only, will cause graph break)
        if compile and backend != "fa2":
            compiled_aten_op = torch.compile(
                torch.ops.aten._flash_attention_forward_no_dropout_inplace
            )
            with _use_backend(backend), torch.no_grad():
                out_buf = torch.empty_like(q_packed)
                compiled_aten_op(
                    out_buf,
                    q_packed,
                    k_pages,
                    v_pages,
                    cu_seq_q,
                    None,
                    max_q,
                    cache_size,
                    0.0,
                    False,
                    False,
                    seqused_k=seqused_k,
                    block_table=block_table,
                )
            self.assertEqual(out_buf, output_reference)

        # With num_splits=1, paged and contiguous must be bit-identical
        if backend == "fa2":
            with _use_backend(backend), torch.no_grad():
                ref_num_splits = varlen_attn(
                    q_packed,
                    k_real_packed,
                    v_real_packed,
                    cu_seq_q,
                    cu_seq_k_real,
                    max_q,
                    max_k_real,
                    num_splits=1,
                )
                paged_num_splits = varlen_attn(
                    q_packed,
                    k_pages,
                    v_pages,
                    cu_seq_q,
                    cu_seq_k_paged,
                    max_q,
                    cache_size,
                    seqused_k=seqused_k,
                    block_table=block_table,
                    num_splits=1,
                )
            self.assertTrue(torch.equal(paged_num_splits, ref_num_splits))