def test_my_empty(self, device, layout, memory_format):
        import libtorch_agn_2_10 as libtorch_agnostic

        deterministic = torch.are_deterministic_algorithms_enabled()
        try:
            # set use_deterministic_algorithms to fill uninitialized memory
            torch.use_deterministic_algorithms(True)

            # Use 4D size for channels_last, 2D otherwise
            size = [2, 3, 4, 5] if memory_format == torch.channels_last else [2, 3]

            # sparse_coo layout doesn't support memory_format parameter
            if layout == torch.sparse_coo and memory_format is not None:
                return

            # Test default parameters
            result = libtorch_agnostic.ops.my_empty(
                size, None, layout, None, None, memory_format
            )
            expected = torch.empty(size, layout=layout, memory_format=memory_format)
            self.assertEqual(result, expected, exact_device=True, exact_layout=True)

            # Test with dtype
            result_float = libtorch_agnostic.ops.my_empty(
                size, torch.float32, layout, None, None, memory_format
            )
            expected_float = torch.empty(
                size,
                dtype=torch.float32,
                layout=layout,
                memory_format=memory_format,
            )
            self.assertEqual(
                result_float, expected_float, exact_device=True, exact_layout=True
            )

            # Test with dtype and device
            result_with_device = libtorch_agnostic.ops.my_empty(
                size, torch.float64, layout, device, None, memory_format
            )
            expected_with_device = torch.empty(
                size,
                dtype=torch.float64,
                layout=layout,
                device=device,
                memory_format=memory_format,
            )
            self.assertEqual(
                result_with_device,
                expected_with_device,
                exact_device=True,
                exact_layout=True,
            )

            # Verify layout if specified
            if layout is not None:
                self.assertEqual(result_with_device.layout, layout)

            # Verify memory format if specified
            if memory_format == torch.channels_last:
                self.assertTrue(
                    result_with_device.is_contiguous(memory_format=torch.channels_last)
                )
            elif memory_format == torch.contiguous_format:
                self.assertTrue(result_with_device.is_contiguous())

            # Test pin_memory on CUDA (only once, not for every parameter combination)
            if device == "cuda" and layout is None and memory_format is None:
                result_pinned = libtorch_agnostic.ops.my_empty(
                    [2, 3], torch.float32, None, "cpu", True, None
                )
                expected_pinned = torch.empty(
                    [2, 3], dtype=torch.float32, device="cpu", pin_memory=True
                )
                self.assertEqual(
                    result_pinned,
                    expected_pinned,
                    exact_device=True,
                    exact_layout=True,
                )
                self.assertTrue(result_pinned.is_pinned())
        finally:
            torch.use_deterministic_algorithms(deterministic)