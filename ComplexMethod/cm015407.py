def test_two_queue_scheduling_off_path_nodes(self):
        """
        Test that off-path nodes (reduce_scatters whose results don't block compute)
        are scheduled near their original position rather than drifting to the end.

        Without two-queue scheduling, off-path nodes get domination=inf and drift
        to end. With two-queue, they stay near original position.
        """

        def func(a, b):
            group_name = "0"
            group_size = 2

            # On-path: all_gather whose result is used by compute
            ag = torch.ops._c10d_functional.all_gather_into_tensor(
                b, group_size, group_name
            )
            ag_out = torch.ops._c10d_functional.wait_tensor(ag)

            # mm1 uses all_gather result (makes ag on-path)
            mm1 = torch.mm(a, ag_out[:4, :4])

            # Off-path: reduce_scatter result not used by further compute
            rs1 = torch.ops._c10d_functional.reduce_scatter_tensor(
                mm1, "sum", group_size, group_name
            )

            mm2 = torch.mm(a, a)
            rs2 = torch.ops._c10d_functional.reduce_scatter_tensor(
                mm2, "sum", group_size, group_name
            )

            mm3 = torch.mm(a, a)

            # Waits at end (like gradient outputs)
            rs1_out = torch.ops._c10d_functional.wait_tensor(rs1)
            rs2_out = torch.ops._c10d_functional.wait_tensor(rs2)

            return mm3.sum() + rs1_out.sum() + rs2_out.sum()

        with FakeTensorMode():
            a = torch.ones(4, 4, device=self.device)
            b = torch.ones(4, 4, device=self.device)
            traced = make_fx(func)(a, b)

        from torch._inductor.fx_passes.overlap_scheduling import (
            schedule_overlap_bucketing,
        )

        def custom_runtime(node: fx.Node, override_size: int | None) -> float | None:
            if "all_gather" in str(node.target) or "reduce_scatter" in str(node.target):
                return 1.0
            return 0.0

        out = schedule_overlap_bucketing(
            traced, custom_runtime_estimation=custom_runtime, max_off_bucket_gb=None
        )

        # Get scheduled order
        node_names = [n.name for n in out.graph.nodes if n.op == "call_function"]
        rs_starts = [
            i
            for i, name in enumerate(node_names)
            if "reduce_scatter" in name and "wait" not in name
        ]
        mm_positions = [i for i, name in enumerate(node_names) if name.startswith("mm")]

        # Off-path reduce_scatters should be interspersed with compute, not all at end
        last_mm = max(mm_positions)
        self.assertTrue(
            any(p < last_mm for p in rs_starts),
            f"Off-path reduce_scatters drifted to end: rs={rs_starts}, mm={mm_positions}, names={node_names}",
        )