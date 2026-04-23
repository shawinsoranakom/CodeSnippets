def test_all_to_all_comm_analysis(self):
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
            chunk = inp.numel() // self.world_size
            split_sizes = [chunk] * self.world_size
            a2a_0_out = torch.ops._c10d_functional.all_to_all_single(
                inp,
                split_sizes,
                split_sizes,
                group_name,
            )
            a2a_0_wait = torch.ops.c10d_functional.wait_tensor(a2a_0_out)
            a2a_1_out = torch.ops._c10d_functional.all_to_all_single(
                a2a_0_wait,
                split_sizes,
                split_sizes,
                group_name,
            )
            a2a_1_wait = torch.ops.c10d_functional.wait_tensor(a2a_1_out)
            return a2a_1_wait

        # test for static shape input estimation
        gm = make_fx(func)(
            torch.ones(group_size * 4, 1, device=self.device), group_size, group_name
        )
        g = gm.graph
        for n in g.nodes:
            if is_all_to_all_tensor(n):
                expected_size = "torch.Size([8, 1])"
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
            if is_all_to_all_tensor(n):
                expected_size = "torch.Size([4*u0, 4])"
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
                # TODO(ruisizhang123): Currently, NCCL estimation API does not support kwargs input
                # (input_split_sizes & output_split_sizes in all-to-all) with dynamic shapes.
                # est_ms_nccl = estimate_nccl_collective_runtime_from_fx_node(
                #     n, use_nccl_estimator=True
                # )
                # assert est_ms_nccl > 0

        # test for backed dynamic shape input estimation
        inp = torch.ones(4, 4, device=self.device)
        torch._dynamo.mark_dynamic(inp, 0, min=1, max=100)
        gm = make_fx(func, tracing_mode="symbolic")(inp, group_size, group_name)
        g = gm.graph
        for n in g.nodes:
            if is_all_to_all_tensor(n):
                expected_size = "torch.Size([2*(((s75**2)//2)), s75])"
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