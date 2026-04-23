def _validate_nt(
        self,
        nt,
        device,
        dtype,
        layout,
        requires_grad,
        dim,
        batch_size,
        contiguous,
        cached_min_seqlen=None,
        cached_max_seqlen=None,
        base=None,
        ref_nt=None,
    ):
        # Validate a bunch of properties after NT construction.
        device = torch.device(device)
        self.assertEqual(nt.dim(), dim)
        self.assertEqual(nt.device, device)
        self.assertEqual(nt.dtype, dtype)
        self.assertEqual(nt.layout, layout)
        self.assertEqual(nt.requires_grad, requires_grad)
        self.assertEqual(nt.is_contiguous(), contiguous)

        if layout == torch.jagged:
            self.assertEqual(nt._values.device, device)
            self.assertEqual(nt._offsets.device, device)
            self.assertEqual(nt.shape[0], batch_size)
            self.assertTrue(isinstance(nt.shape[1], torch.SymInt))

            if base is not None:
                self.assertTrue(nt._is_view() and nt._base is base)
                replay_cache = nt._view_func(torch.randn_like(nt._base))._metadata_cache
                self.assertEqual(
                    "min_seqlen" in replay_cache, cached_min_seqlen is not None
                )
                self.assertEqual(
                    "max_seqlen" in replay_cache, cached_max_seqlen is not None
                )

            self.assertEqual(
                "min_seqlen" in nt._metadata_cache, cached_min_seqlen is not None
            )
            self.assertEqual(
                "max_seqlen" in nt._metadata_cache, cached_max_seqlen is not None
            )

            if cached_min_seqlen is not None:
                self.assertEqual(nt._min_seqlen, cached_min_seqlen)

            if cached_max_seqlen is not None:
                self.assertEqual(nt._max_seqlen, cached_max_seqlen)

        if ref_nt is not None:
            self.assertEqual(nt.size(0), ref_nt.size(0))
            for n1, n2 in zip(nt.unbind(), ref_nt.unbind()):
                self.assertEqual(n1, n2)