def test_index_add(self):
        for device in get_all_device_types():
            for dest_contig, src_contig, index_contig in product([True, False], repeat=3):
                for other_sizes in ((), (4, 5)):
                    for dtype in [torch.int, torch.long]:
                        num_copy, num_dest = 3, 3
                        dest = torch.randn(num_dest, *other_sizes, device=device)
                        if not dest_contig:
                            dest = make_tensor(dest.shape, device=device, dtype=dest.dtype, noncontiguous=True)
                        src = torch.randn(num_copy, *other_sizes, device=device)
                        if not src_contig:
                            src = noncontiguous_like(src)
                        idx = torch.randperm(num_dest, dtype=dtype, device=device).narrow(0, 0, num_copy)
                        if not index_contig:
                            idx = noncontiguous_like(idx)
                        # index_add_ without alpha argument
                        dest2 = dest.clone()
                        dest.index_add_(0, idx, src)
                        for i in range(idx.size(0)):
                            dest2[idx[i]] += src[i]
                        self.assertEqual(dest, dest2)
                        # index_add_ with alpha argument
                        dest2 = dest.clone()
                        dest.index_add_(0, idx, src, alpha=2)
                        for i in range(idx.size(0)):
                            dest2[idx[i]] += src[i] * 2
                        self.assertEqual(dest, dest2)