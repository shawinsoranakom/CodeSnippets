def _test_partial_flattening(self, half: bool):
        module = self._get_transformer()
        if half:
            module = module.half()
        numel = sum(p.numel() for p in module.parameters())

        encoder_1_params = list(module.encoder.layers[1].parameters())
        decoder_0_params = list(module.decoder.layers[0].parameters())
        params_to_flatten = encoder_1_params + decoder_0_params
        num_params = [len(encoder_1_params), len(decoder_0_params)]
        numel_to_flatten = sum(p.numel() for p in params_to_flatten)
        module.encoder.layers[1] = FSDP(module.encoder.layers[1])
        module.decoder.layers[0] = FSDP(module.decoder.layers[0])
        flat_params = [
            module.encoder.layers[1]._flat_param,
            module.decoder.layers[0]._flat_param,
        ]

        self.assertEqual(sum(fp.numel() for fp in flat_params), numel_to_flatten)
        self.assertEqual(sum(p.numel() for p in module.parameters()), numel)

        # Check that flattened parameters have been replaced with a single
        # `FlatParameter`
        self.assertEqual(len(list(module.encoder.layers[1].parameters())), 1)
        self.assertEqual(len(list(module.decoder.layers[0].parameters())), 1)

        # Check that non-flattened parameters remain
        self.assertEqual(
            len(list(module.encoder.layers[0].parameters())), num_params[0]
        )
        self.assertEqual(
            len(list(module.decoder.layers[1].parameters())), num_params[1]
        )

        # Check that calling `module.to()` affects the `FlatParameter`s
        orig_dtype = params_to_flatten[0].dtype
        new_dtype = torch.float32 if orig_dtype == torch.float16 else torch.float16
        for flat_param in flat_params:
            self.assertEqual(flat_param.dtype, orig_dtype)
        self.assertTrue(
            all(p.dtype == orig_dtype for p in module.encoder.layers[0].parameters())
        )
        module = module.to(dtype=new_dtype)
        for flat_param in flat_params:
            self.assertEqual(flat_param.dtype, new_dtype)
        self.assertTrue(
            all(p.dtype == new_dtype for p in module.encoder.layers[0].parameters())
        )