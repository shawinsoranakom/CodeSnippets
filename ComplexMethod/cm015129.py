def test_put(self, device, dtype):
        src_size = (4,)

        make_arg = partial(make_tensor, device=device, dtype=dtype)
        make_idx = partial(make_tensor, low=0, device=device, dtype=torch.int64)

        def ref_put(dst, idx, src, accumulate):
            new_dst = dst.clone(memory_format=torch.contiguous_format).view(-1)
            new_idx = idx.contiguous().view(-1)
            new_src = src.contiguous().view(-1)
            method = new_dst.index_add_ if accumulate else new_dst.index_copy_
            return method(0, new_idx, new_src).view_as(dst)

        for dst_contig, src_contig, idx_contig, idx_reshape, accumulate in product([True, False], repeat=5):
            for dst_size in ((5,), (4, 5)):
                dst = make_arg(dst_size, noncontiguous=not dst_contig)
                src = make_arg(src_size, noncontiguous=not src_contig)

                # If accumulate=True, `put_` should be deterministic regardless of the inputs on CPU
                # On CUDA it may not be, but the test has enough tolerance to account for this
                if accumulate:
                    idx = make_idx(src_size, high=dst.numel())
                else:
                    idx = torch.randperm(dst.numel(), dtype=torch.int64, device=device)[:src_size[0]]
                if not idx_contig:
                    idx = torch.repeat_interleave(idx, 2, dim=-1)[..., ::2]
                if idx_reshape:
                    idx = idx.reshape(2, 2)
                out = torch.put(dst, idx, src, accumulate)
                # out-place
                reference = ref_put(dst, idx, src, accumulate)
                self.assertEqual(out, reference)

                # in-place
                dst.put_(idx, src, accumulate)
                self.assertEqual(dst, reference)


        # Create the 8 possible combinations of scalar sizes for target / index / source
        scalars = ((make_arg(size_t),
                    make_idx(size_i, high=1),
                    make_arg(size_s))
                   for size_t, size_i, size_s in product([(), (1,)], repeat=3))
        for (dest, idx, source), accumulate in product(scalars, [True, False]):
            dest_init = dest.clone()
            # out-place
            out = torch.put(dest, idx, source, accumulate=accumulate)
            # in-place
            dest1 = dest.clone()
            dest1.put_(idx, source, accumulate=accumulate)
            for d in [out, dest1]:
                if accumulate:
                    self.assertEqual(d.item(), (dest_init + source).item())
                else:
                    self.assertEqual(d.item(), source.item())

        # Empty case
        dest = make_arg((3, 2))
        reference = dest.clone()
        idx = make_idx((0,), high=1)
        source = make_arg((0,))
        for accumulate in [True, False]:
            out = torch.put(dest, idx, source, accumulate=accumulate)
            self.assertEqual(out, reference)
            dest.put_(idx, source, accumulate=accumulate)
            self.assertEqual(dest, reference)