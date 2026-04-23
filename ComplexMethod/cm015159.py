def test_sparse_tensor_multiprocessing(self, device, context):
        # The 'fork' multiprocessing context doesn't work for CUDA so skip it
        if "cuda" in device and context == "fork":
            self.skipTest(
                f"{context} multiprocessing context not supported for {device}"
            )

        dataset = [torch.randn(5, 5).to_sparse().to(device) for _ in range(10)]

        pin_memory_settings = [False]
        if device == "cpu" and torch.cuda.is_available():
            pin_memory_settings.append(True)

        for pin_memory in pin_memory_settings:
            loader = torch.utils.data.DataLoader(
                dataset,
                batch_size=1,
                num_workers=4,
                collate_fn=_sparse_coo_collate,
                pin_memory=pin_memory,
                multiprocessing_context=context,
            )

            for i, batch in enumerate(loader):
                self.assertEqual(batch[0], dataset[i])