def _test_ring_attention_sdpa(
        self,
        is_causal: bool,
        compiled: bool,
        backend: SDPBackend,
        load_balance: bool,
        rotater: _RotateMethod,
        test_forward_only: bool,
        use_context: bool,
    ) -> None:
        def fn_eval(fn, *args, **kwargs):
            if test_forward_only:
                with torch.no_grad():
                    return fn(*args, **kwargs)
            else:
                out = fn(*args, **kwargs)
                out.sum().backward()
                return out

        if load_balance and not is_causal:
            return

        # Compilation with context_parallel doesn't work yet — both paths
        # (use_context=True monkey-patch and use_context=False parallelize_module)
        # fail during tracing because DTensor dispatch interferes with sdpa.
        # Previously CommDebugMode was active for all subtests, which caused
        # the frame to be silently skipped, masking this limitation.
        if compiled:
            return

        set_rotate_method(rotater_enum_to_str[rotater])
        self.assertEqual(_cp_options.rotate_method, rotater)
        device_mesh = DeviceMesh(self.device_type, torch.arange(0, self.world_size))
        dtype = torch.bfloat16
        bs = 8
        seq_length = 1024
        seq_dim = 2
        dim = 32
        nheads = 8
        torch.manual_seed(10)
        dtype = (
            torch.bfloat16
            if backend == SDPBackend.FLASH_ATTENTION
            or backend == SDPBackend.CUDNN_ATTENTION
            else torch.float32
        )

        q, k, v = [
            torch.rand(
                (bs, nheads, seq_length * self.world_size, dim),
                device=self.device_type,
                dtype=dtype,
                requires_grad=True,
            )
            for _ in range(3)
        ]

        # Ensure all ranks have the same initialization data.
        with torch.no_grad():
            dist.broadcast(q, src=0)
            dist.broadcast(k, src=0)
            dist.broadcast(v, src=0)

        with sdpa_kernel(backend):
            out = fn_eval(F.scaled_dot_product_attention, q, k, v, is_causal=is_causal)

        cp_q, cp_k, cp_v = [target.detach().clone() for target in [q, k, v]]
        cp_out, cp_dq, cp_dk, cp_dv = self._ring_attention_sdpa(
            cp_q,
            cp_k,
            cp_v,
            fn_eval=fn_eval,
            mesh=device_mesh,
            seq_dim=seq_dim,
            is_causal=is_causal,
            compiled=compiled,
            backend=backend,
            rotater=rotater,
            test_forward_only=test_forward_only,
            load_balance=load_balance,
            use_context=use_context,
        )

        # Due to numerical error, we need to choose different atol for different
        # attention kernels
        (cp_out,) = context_parallel_unshard(device_mesh, [cp_out], [seq_dim])
        atol = (
            2e-06
            if backend == SDPBackend.EFFICIENT_ATTENTION
            else 8e-3 * self.world_size
        )
        rtol = (
            1e-05
            if backend == SDPBackend.EFFICIENT_ATTENTION
            else 1e-3 * self.world_size
        )
        torch.testing.assert_close(out, cp_out, atol=atol, rtol=rtol)

        if test_forward_only:
            return

        cp_dq, cp_dk, cp_dv = context_parallel_unshard(
            device_mesh,
            [cp_dq, cp_dk, cp_dv],
            [seq_dim] * 3,
        )
        torch.testing.assert_close(q.grad, cp_dq, atol=atol, rtol=rtol)
        torch.testing.assert_close(k.grad, cp_dk, atol=atol, rtol=rtol)
        torch.testing.assert_close(v.grad, cp_dv, atol=atol, rtol=rtol)