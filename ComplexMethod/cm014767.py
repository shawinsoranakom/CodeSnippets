def test_profiler_sequence_nr(self):
        with torch.profiler.profile() as prof:
            values = torch.randn(4, 6, requires_grad=True)
            offsets = torch.tensor([0, 2, 4])
            values = values * 2
            l = torch.nn.Linear(6, 8)
            nt = torch.nested.nested_tensor_from_jagged(values, offsets)

            nt = l(nt)
            val = nt.values()

            loss = val.sum()
            loss.backward()

        fwd_seq_nrs = []
        for evt in prof.events():
            if (
                "linear" in evt.name.lower()
                and "backward" not in evt.name.lower()
                and evt.sequence_nr != -1
            ):
                fwd_seq_nrs.append(evt.sequence_nr)

        bwd_seq_nrs = []
        for evt in prof.events():
            if (
                "linear" in evt.name.lower()
                and "backward" in evt.name.lower()
                and "evaluate_function" not in evt.name.lower()
                and evt.sequence_nr != -1
            ):
                bwd_seq_nrs.append(evt.sequence_nr)

        # There should only be one such event with a sequence number:
        # the PythonTLSSnapshot event - but, note that it's not terrible if
        # we end up with multiple events with the same sequence number - so we
        # could relax this check if it becomes inconvenient to maintain this
        # property.
        self.assertEqual(len(fwd_seq_nrs), 1)
        self.assertEqual(len(bwd_seq_nrs), 1)
        self.assertEqual(fwd_seq_nrs[0], bwd_seq_nrs[0])