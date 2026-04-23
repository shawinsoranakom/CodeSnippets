def test_foreach_placement_propagation(
        self, op_fn, second_arg, placement, expected
    ):
        device_mesh = self.build_device_mesh()
        comm_mode = CommDebugMode()

        shapes = [(8, 8), (4, 4), (2, 6)]
        if placement.is_shard():
            dts = [
                distribute_tensor(
                    torch.rand(s, device=self.device_type), device_mesh, [placement]
                )
                for s in shapes
            ]
        else:
            dts = [
                DTensor.from_local(
                    torch.rand(s, device=self.device_type), device_mesh, [placement]
                )
                for s in shapes
            ]

        if second_arg == "list":
            if placement.is_shard():
                args = [
                    distribute_tensor(
                        torch.rand(s, device=self.device_type),
                        device_mesh,
                        [placement],
                    )
                    for s in shapes
                ]
            else:
                args = [
                    DTensor.from_local(
                        torch.rand(s, device=self.device_type),
                        device_mesh,
                        [placement],
                    )
                    for s in shapes
                ]
            call_args = (dts, args)
        elif second_arg is None:
            call_args = (dts,)
        else:
            call_args = (dts, second_arg)

        with comm_mode:
            result = op_fn(*call_args)

        self.assertEqual(comm_mode.get_total_counts(), 0)
        self.assertEqual(len(result), len(shapes))
        for r in result:
            self.assertIsInstance(r, DTensor)
            self.assertEqual(r.placements, (expected,))