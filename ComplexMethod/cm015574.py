def _ring_attention_sdpa(
        self,
        cp_q: torch.Tensor,
        cp_k: torch.Tensor,
        cp_v: torch.Tensor,
        *,
        fn_eval: Callable,
        mesh: DeviceMesh,
        seq_dim: int,
        is_causal: bool,
        compiled: bool,
        backend: SDPBackend,
        rotater: _RotateMethod,
        test_forward_only: bool,
        load_balance: bool,
        use_context: bool,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        if not use_context:
            cp_plan = _ContextParallel(
                seq_dim=seq_dim,
                attention_type=_ContextParallel.AttentionType.SDPA,
            )
            attention = SDPAWrapper(compiled=compiled, backend=backend)
            attention = parallelize_module(attention, mesh, cp_plan)
            if load_balance:
                seq_len = cp_q.size(seq_dim)
                load_balancer = _HeadTailLoadBalancer(seq_len, mesh.size(), cp_q.device)
            else:
                load_balancer = None
            cp_q, cp_k, cp_v = _context_parallel_shard(
                mesh, (cp_q, cp_k, cp_v), (seq_dim,) * 3, load_balancer=load_balancer
            )
            _enable_context_parallel_dispatcher()
        else:
            # Theoretically, context_parallel() should not be used to shard
            # parameters because when require_grad is True, resize_ is not
            # allowed. But requires_grad of cp_q, cp_k, and cp_v are False
            # now. So we can just use context_parallel() to shard q, k, v.
            # In reality, context_parallel() should be used to shard the input.
            # In reality, context_parallel() should only be used to shard
            # the model inputs (batch).

            _cp_options.enable_load_balance = load_balance
            cp_context = context_parallel(
                mesh, buffers=(cp_q, cp_k, cp_v), buffer_seq_dims=(seq_dim,) * 3
            )
            cp_context.__enter__()

            # NOTE: This demonstrates that monkey patching is not fully reliable.
            # If we use SDPAWrapper directly, the monkey patching dispatch mode
            # does not function correctly. To ensure proper behavior,
            # F.scaled_dot_product_attention must be referenced within the
            # context_parallel() scope.
            attention = F.scaled_dot_product_attention
            if compiled:
                attention = torch.compile(
                    attention, fullgraph=True, backend="aot_eager"
                )

        for target in [cp_q, cp_k, cp_v]:
            target.requires_grad = True

        check_comm_counts = not compiled and rotater == _RotateMethod.ALL_TO_ALL
        comm_mode = CommDebugMode() if check_comm_counts else contextlib.nullcontext()
        with comm_mode:
            with sdpa_kernel(backend):
                cp_out = fn_eval(
                    attention,
                    cp_q,
                    cp_k,
                    cp_v,
                    is_causal=is_causal,
                )

            if check_comm_counts:
                expect_all2all_count = (
                    self.world_size - 1
                    if test_forward_only
                    else self.world_size * 3 - 2
                )
                self.assertDictEqual(
                    comm_mode.get_comm_counts(),
                    {c10d_functional.all_to_all_single: expect_all2all_count},
                )
        cp_dq, cp_dk, cp_dv = cp_q.grad, cp_k.grad, cp_v.grad
        for target in [cp_q, cp_k, cp_v]:
            target.requires_grad = False

        if not use_context:
            _disable_context_parallel_dispatcher()
        else:
            cp_context.__exit__(None, None, None)

        return cp_out, cp_dq, cp_dk, cp_dv