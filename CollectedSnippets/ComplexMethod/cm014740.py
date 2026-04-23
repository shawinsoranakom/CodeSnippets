def test_masked_softmax_mask_types(self, device):
        # Test that mask type 0 (LxL attention mask), mask type 1 (BxL padding mask),
        # and mask type 2 (generic BxHxLxL mask) are processed correctly on the
        # fast path and the results match explicit slow calculation.
        sizes = [(1, 1, 32), (3, 16, 310), (12, 4, 1024), (4, 2, 1200)]

        for (B, num_heads, L) in sizes:

            # mask_type == 0 => attention mask of shape LxL
            src_mask_orig = torch.randint(0, 2, (L, L)).bool()
            src_mask = src_mask_orig.reshape(1, 1, L, L).expand(B, num_heads, L, L).bool()

            # mask_type == 1 => padding mask of shape BxL
            src_key_padding_mask_orig = torch.randint(0, 2, (B, L)).bool()
            src_key_padding_mask = src_key_padding_mask_orig.reshape(B, 1, 1, L).expand(B, num_heads, L, L).bool()

            # mask_type == 2 =>  shape BxHxLxL
            generic_mask = torch.randint(0, 2, (B, num_heads, L, L)).bool()
            masks = [(src_mask_orig, src_mask, 0),
                     (src_key_padding_mask_orig, src_key_padding_mask, 1),
                     (generic_mask, generic_mask, 2)
                     ]
            for dim in [0, 3]:
                for mask_orig, mask, mask_type in masks:
                    if (self.device_type == "cuda") and (num_heads % 2) and (mask_type == 1):
                        # CUDA path doesn't support padding mask when the number of heads is odd
                        continue
                    input = torch.randn((B, num_heads, L, L))
                    if (self.device_type == "cuda"):
                        input = input.cuda()
                        mask = mask.cuda()
                        mask_orig = mask_orig.cuda()
                    native_res = torch._masked_softmax(input, mask_orig, dim, mask_type)
                    mask = ~mask

                    def slow_masked_softmax(input, mask):
                        exp = torch.exp(input)
                        exp = exp * mask
                        s = exp.sum(dim=dim, keepdim=True).expand(exp.size())
                        return exp / s

                    pt_res = slow_masked_softmax(input, mask)
                    pt_res = torch.nan_to_num(pt_res)

                    mask_not = mask.logical_not()
                    # In result, should only fill the entirely masked out rows since those are non-deterministic (*may* be 0)
                    # Converts rows with all True's to False
                    mask_out = mask_not.all(dim, keepdim=True).expand(mask_not.shape)
                    self.assertEqual(
                        pt_res.masked_fill(mask_out, 0),
                        native_res.masked_fill(mask_out, 0),
                        exact_dtype=True
                    )