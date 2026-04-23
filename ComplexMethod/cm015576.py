def _test_cp_flex_attention(
        self,
        *,
        qkv_size: int,
        B: int = 1,
        block_mask,
        lb_type: str,
        document_lengths: list[list[int]] | None = None,
    ) -> None:
        torch.use_deterministic_algorithms(True)
        torch.cuda.manual_seed(1234)

        dtype = torch.float32
        bs = B if B > 1 else 8
        dim = 32
        nheads = 8
        seq_dim = 2
        lb = self._get_load_balancer(
            lb_type,
            {
                "seq_length": qkv_size,
                "document_lengths": document_lengths,
                "block_mask": block_mask,
            },
        )

        qkv = [
            torch.rand(
                (bs, nheads, qkv_size, dim),
                device=self.device_type,
                dtype=dtype,
                requires_grad=True,
            )
            for _ in range(3)
        ]

        expect_out, expect_aux = compiled_flex_attention(
            *qkv, block_mask=block_mask, return_aux=AuxRequest(lse=True)
        )
        expect_out.sum().backward()

        # Prepare the required global vars for CP+Flex:
        device_mesh = init_device_mesh(
            device_type=self.device_type,
            mesh_shape=(self.world_size,),
            mesh_dim_names=("cp",),
        )

        flex_attention_wrapper_module = FlexAttentionWrapper()
        cp_plan = _ContextParallel(
            seq_dim=seq_dim,
            attention_type=_ContextParallel.AttentionType.FLEX,
        )
        parallelize_module(
            flex_attention_wrapper_module,
            device_mesh,
            cp_plan,
        )

        *cp_qkv, cp_block_mask = _context_parallel_shard(
            device_mesh,
            [t.detach().clone() for t in qkv] + [block_mask],
            [seq_dim] * 4,
            load_balancer=lb,
        )
        for t in cp_qkv:
            t.requires_grad = True

        cp_out, cp_aux = flex_attention_wrapper_module(
            *cp_qkv,
            block_mask=cp_block_mask,
            return_aux=AuxRequest(lse=True),
        )

        # backward run
        cp_out.sum().backward()

        atol = 2e-06
        rtol = 1e-05
        # unshard the output
        cp_out, cp_lse = context_parallel_unshard(
            device_mesh,
            buffers=[cp_out, cp_aux.lse],
            seq_dims=[seq_dim] * 2,
            load_balancer=lb,
        )
        torch.testing.assert_close(cp_out, expect_out, atol=atol, rtol=rtol)
        torch.testing.assert_close(cp_lse, expect_aux.lse, atol=atol, rtol=rtol)

        # unshard the gradient
        cp_qkv_grad = context_parallel_unshard(
            device_mesh,
            buffers=[t.grad for t in cp_qkv],
            seq_dims=[seq_dim] * 3,
            load_balancer=lb,
        )

        qkv_grad = [t.grad for t in qkv]
        for grad, cp_grad in zip(qkv_grad, cp_qkv_grad):
            torch.testing.assert_close(grad, cp_grad, atol=atol, rtol=rtol)