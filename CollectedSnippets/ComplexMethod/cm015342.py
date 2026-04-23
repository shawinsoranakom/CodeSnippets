def zerodim_test_core(self, device_pairs):
        # Test the support of zerodim tensors with non-zerodim tensors
        def mul(x, y):
            return x * y

        def add(x, y):
            return x + y

        fns = [mul, add]

        input_shapes = [
            ((1, 2, 2), (2, 2)),  # Different dim, non-zerodim
            ((1, 2, 2), ()),  # one zerodim
            ((), ()),  # both zerodim
        ]

        for fn, shapes, devices in product(fns, input_shapes, device_pairs):
            subtest_str = f"{fn.__name__} \n shapes: {shapes}, \n devices: {devices}"
            in0 = torch.rand(shapes[0], device=devices[0])
            in1 = torch.rand(shapes[1], device=devices[1])

            try:
                out = fn(in0, in1)
            except Exception as e:
                # Don't expect eager failures for CPU zerodim tensors
                for i in range(len(devices)):
                    if shapes[i] == () and devices[i] == self.cpu:
                        raise e

                # only expect eager failures on different devices
                if devices[0] == devices[1]:
                    raise e

                # Expect result device to be None for the failure cases.
                self.assert_device_equal(fn, devices, None, shapes, subtest_str)
                continue

            self.assert_device_equal(fn, devices, out.device, shapes, subtest_str)

            # Test that without shapes, we either get the same device or None for the device
            # Aka that the code is convservative for tensor shapes.
            graph = torch.jit.script(fn).graph
            self.prop_device_on_graph(graph, devices)
            actual_device = self.node_output_device(graph)
            self.assertTrue(
                (actual_device is None) or (actual_device.type == out.device.type)
            )