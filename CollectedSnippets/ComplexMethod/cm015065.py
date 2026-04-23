def test_custom_op_registration(self, device, dtype, sdpa_backend=None):
        if TEST_WITH_ROCM:
            torch.backends.cuda.preferred_rocm_fa_library(sdpa_backend)
        torch.manual_seed(42)

        shape = VarlenShape(batch_size=2, max_seq_len=512, embed_dim=1024, num_heads=16)

        attention_block = AttentionBlock(
            shape.embed_dim, shape.num_heads, device, dtype
        )

        total_tokens = shape.batch_size * shape.max_seq_len
        x_packed = torch.randn(
            total_tokens,
            shape.embed_dim,
            device=device,
            dtype=dtype,
            requires_grad=True,
        )
        cu_seq = torch.tensor(
            [0, shape.max_seq_len, total_tokens], device=device, dtype=torch.int32
        )

        compiled_forward = torch.compile(
            attention_block.forward_varlen, backend="eager"
        )
        with OpLoggingMode() as mode:
            output = compiled_forward(x_packed, cu_seq, shape.max_seq_len)

            varlen_grad_out = torch.ones_like(output)
            _ = torch.autograd.grad(
                outputs=output,
                inputs=x_packed,
                grad_outputs=varlen_grad_out,
                retain_graph=True,
                create_graph=False,
                allow_unused=False,
            )[0]

        called_ops = mode.called_ops

        custom_ops_called = any(
            "torch_attn._varlen_attn" in op for op in called_ops
        ) and any("torch_attn._varlen_attn_backward" in op for op in called_ops)
        if not custom_ops_called:
            raise AssertionError("custom varlen attention ops should have been called")

        # Also verify _varlen_attn_out dispatches correctly under compile
        q, k, v = attention_block.get_varlen_qkv(x_packed.detach())

        def run_varlen_out(q, k, v, cu_seq, max_len):
            out_buf = torch.empty_like(q)
            varlen_attn_out(out_buf, q, k, v, cu_seq, cu_seq, max_len, max_len)
            return out_buf

        compiled_out = torch.compile(run_varlen_out, backend="eager")
        with OpLoggingMode() as out_mode:
            compiled_out(q, k, v, cu_seq, shape.max_seq_len)

        if not any("torch_attn._varlen_attn_out" in op for op in out_mode.called_ops):
            raise AssertionError("custom _varlen_attn_out op should have been called")