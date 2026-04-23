def test_profiler_seq_nr(self):
        with profile(use_kineto=kineto_available()) as p:
            x = torch.randn(10, 10, requires_grad=True)
            y = torch.randn(10, 10, requires_grad=True)
            z = x + y
            s = z.sum(dim=None)
            s.backward()
        print(p.key_averages().table(sort_by="self_cpu_time_total", row_limit=-1))
        # expecting aten::add, aten::sum to have the sequence numbers,
        # expecting the corresponding backward nodes to have the same numbers
        # as the forward ops
        autograd_ops = {
            ("aten::add", "Add"): [],
            ("aten::sum", "Sum"): [],
        }
        accumulate_ops = []
        found_empty = False
        for e in p.function_events:
            for (fwd_name, bwd_name), ops in autograd_ops.items():
                if e.name == fwd_name or (bwd_name in e.name and "Backward" in e.name):
                    ops.append(e)

            if "AccumulateGrad" in e.name:
                accumulate_ops.append(e)

            # check that nested ops (e.g. empty) don't have
            # sequence number
            if e.name == "aten::empty":
                self.assertEqual(e.sequence_nr, -1)
                found_empty = True

        for idx, ((fwd_name, bwd_name), ops) in enumerate(autograd_ops.items()):
            self.assertEqual(len(ops), 3)
            self.assertEqual(ops[0].name, fwd_name)
            self.assertEqual(
                ops[1].name,
                f"autograd::engine::evaluate_function: {bwd_name}Backward{idx}",
            )
            self.assertEqual(ops[2].name, f"{bwd_name}Backward{idx}")
            self.assertGreaterEqual(ops[0].sequence_nr, 0)
            self.assertEqual(ops[1].sequence_nr, ops[0].sequence_nr)
            self.assertEqual(ops[2].sequence_nr, ops[0].sequence_nr)
            self.assertEqual(ops[0].fwd_thread, 0)
            self.assertEqual(ops[1].fwd_thread, ops[0].thread)
            self.assertEqual(ops[2].fwd_thread, ops[0].thread)
        self.assertTrue(found_empty)