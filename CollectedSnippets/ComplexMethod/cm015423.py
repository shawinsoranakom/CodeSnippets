def test_all_reduce_comm_analysis(self):
        store = c10d.FileStore(self.file_name, self.world_size)
        torch.cuda.set_device(self.rank)
        c10d.init_process_group(
            backend="nccl", store=store, rank=self.rank, world_size=self.world_size
        )
        group = c10d.distributed_c10d._get_default_group()
        group_name = "default"
        torch._C._distributed_c10d._register_process_group(
            group_name, torch.distributed.group.WORLD
        )
        group_size = group.size()

        def func(inp, group_size, group_name):
            ar_0_out = torch.ops._c10d_functional.all_reduce(inp, "sum", group_name)
            ar_0_wait = torch.ops.c10d_functional.wait_tensor(ar_0_out)
            ar_1_out = torch.ops._c10d_functional.all_reduce(
                ar_0_wait, "sum", group_name
            )
            ar_1_wait = torch.ops.c10d_functional.wait_tensor(ar_1_out)
            return ar_1_wait

        # test for static shape input estimation
        gm = make_fx(func)(torch.ones(4, 4, device=self.device), group_size, group_name)
        g = gm.graph
        for n in g.nodes:
            if is_all_reduce_tensor(n):
                expected_size = "torch.Size([4, 4])"
                if str(n.meta["val"].size()) != expected_size:
                    raise AssertionError(
                        f"Expected size {expected_size}, got {n.meta['val'].size()}"
                    )
                from torch._inductor.comm_analysis import (
                    estimate_nccl_collective_runtime_from_fx_node,
                )

                est_ms = estimate_nccl_collective_runtime_from_fx_node(
                    n, use_nccl_estimator=False
                )
                if not (est_ms > 0):
                    raise AssertionError(f"Expected est_ms > 0, got {est_ms}")
                est_ms_nccl = estimate_nccl_collective_runtime_from_fx_node(
                    n, use_nccl_estimator=True
                )
                if not (est_ms_nccl > 0):
                    raise AssertionError(f"Expected est_ms_nccl > 0, got {est_ms_nccl}")

        # test for unbacked dynamic shape input estimation
        class TestModule(nn.Module):
            def __init__(self, group_size, group_name):
                super().__init__()
                self.group_size = group_size
                self.group_name = group_name

            def forward(self, x):
                u = x.item()
                # Use u as a dimension of a new tensor:
                y = torch.empty(u, 4, device=x.device)
                return func(y, self.group_size, self.group_name)

        inp = torch.tensor(1, device=self.device)
        model = TestModule(group_size, group_name).to(self.device)
        exported_program = torch.export.export(
            model,
            (inp,),
        )
        gm = exported_program.module()
        g = gm.graph
        for n in g.nodes:
            if is_all_reduce_tensor(n):
                expected_size = "torch.Size([u0, 4])"
                if str(n.meta["val"].size()) != expected_size:
                    raise AssertionError(
                        f"Expected size {expected_size}, got {n.meta['val'].size()}"
                    )
                from torch._inductor.comm_analysis import (
                    estimate_nccl_collective_runtime_from_fx_node,
                )

                est_ms = estimate_nccl_collective_runtime_from_fx_node(
                    n, use_nccl_estimator=False
                )
                if not (est_ms > 0):
                    raise AssertionError(f"Expected est_ms > 0, got {est_ms}")
                est_ms_nccl = estimate_nccl_collective_runtime_from_fx_node(
                    n, use_nccl_estimator=True
                )
                if not (est_ms_nccl > 0):
                    raise AssertionError(f"Expected est_ms_nccl > 0, got {est_ms_nccl}")

        # test for backed dynamic shape input estimation
        inp = torch.ones(4, 4, device=self.device)
        torch._dynamo.mark_dynamic(inp, 0, min=1, max=100)
        gm = make_fx(func, tracing_mode="symbolic")(inp, group_size, group_name)
        g = gm.graph
        for n in g.nodes:
            if is_all_reduce_tensor(n):
                expected_size = "torch.Size([s75, s75])"
                if str(n.meta["val"].size()) != expected_size:
                    raise AssertionError(
                        f"Expected size {expected_size}, got {n.meta['val'].size()}"
                    )
                from torch._inductor.comm_analysis import (
                    estimate_nccl_collective_runtime_from_fx_node,
                )

                est_ms = estimate_nccl_collective_runtime_from_fx_node(
                    n, use_nccl_estimator=False
                )
                if not (est_ms > 0):
                    raise AssertionError(f"Expected est_ms > 0, got {est_ms}")
                est_ms_nccl = estimate_nccl_collective_runtime_from_fx_node(
                    n, use_nccl_estimator=True
                )
                if not (est_ms_nccl > 0):
                    raise AssertionError(f"Expected est_ms_nccl > 0, got {est_ms_nccl}")