def test_nested_tensor_from_jagged(self, device, dtype, pass_min_max):
        # === construct from (values, offsets) ===
        values = torch.randn(10, 5, device=device, dtype=dtype)
        offsets = torch.tensor([0, 2, 4, 6, 10], device=device, dtype=torch.int64)

        # compute min / max seqlen
        lengths = offsets.diff()
        min_seqlen = lengths.min().item()
        max_seqlen = lengths.max().item()

        if pass_min_max:
            nt = torch.nested.nested_tensor_from_jagged(
                values, offsets=offsets, min_seqlen=min_seqlen, max_seqlen=max_seqlen
            )
        else:
            nt = torch.nested.nested_tensor_from_jagged(values, offsets=offsets)
        self._validate_nt(
            nt,
            device,
            dtype,
            torch.jagged,
            requires_grad=False,
            dim=3,
            batch_size=4,
            contiguous=True,
            cached_min_seqlen=(min_seqlen if pass_min_max else None),
            cached_max_seqlen=(max_seqlen if pass_min_max else None),
            base=values,
        )

        # === construct from (values, offsets, lengths) ===
        lengths = torch.tensor([2, 1, 1, 2], device=device)

        # compute min / max seqlen
        min_seqlen = lengths.min().item()
        max_seqlen = lengths.max().item()

        if pass_min_max:
            nt = torch.nested.nested_tensor_from_jagged(
                values,
                offsets=offsets,
                lengths=lengths,
                min_seqlen=min_seqlen,
                max_seqlen=max_seqlen,
            )
        else:
            nt = torch.nested.nested_tensor_from_jagged(
                values, offsets=offsets, lengths=lengths
            )

        # when both offsets / lengths are specified, expect non-contiguous
        self._validate_nt(
            nt,
            device,
            dtype,
            torch.jagged,
            requires_grad=False,
            dim=3,
            batch_size=4,
            contiguous=False,
            cached_min_seqlen=(min_seqlen if pass_min_max else None),
            cached_max_seqlen=(max_seqlen if pass_min_max else None),
            base=values,
        )
        self.assertIs(nt.lengths(), lengths)

        # === construct from (values, lengths) ===
        values = torch.randn(14, 5, device=device, dtype=dtype)
        lengths = torch.tensor([2, 3, 4, 5], device=device)

        # compute min / max seqlen
        min_seqlen = lengths.min().item()
        max_seqlen = lengths.max().item()

        if pass_min_max:
            nt = torch.nested.nested_tensor_from_jagged(
                values, lengths=lengths, min_seqlen=min_seqlen, max_seqlen=max_seqlen
            )
        else:
            nt = torch.nested.nested_tensor_from_jagged(values, lengths=lengths)

        # for now, if only lengths is specified, convert to offsets to integrate best with the
        # existing kernels
        expected_offsets = torch.tensor([0, 2, 5, 9, 14], device=device)
        expected_nt = torch.nested.nested_tensor_from_jagged(
            values, offsets=expected_offsets
        )
        self._validate_nt(
            nt,
            device,
            dtype,
            torch.jagged,
            requires_grad=False,
            dim=3,
            batch_size=4,
            contiguous=True,
            cached_min_seqlen=(min_seqlen if pass_min_max else None),
            cached_max_seqlen=(max_seqlen if pass_min_max else None),
            base=values,
            ref_nt=expected_nt,
        )

        # error case: no offsets or lengths
        with self.assertRaisesRegex(
            RuntimeError, "At least one of offsets or lengths is required"
        ):
            torch.nested.nested_tensor_from_jagged(values, offsets=None, lengths=None)

        with self.assertRaisesRegex(ValueError, "Expected jagged_dim >=1, but got 0."):
            torch.nested.nested_tensor_from_jagged(
                values, lengths=lengths, jagged_dim=0
            )