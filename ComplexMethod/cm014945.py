def test_histogramdd(self, device, dtype):
        shapes = (
            (1, 5),
            (3, 5),
            (1, 5, 1),
            (2, 3, 5),
            (7, 7, 7, 7),
            (16, 8, 4, 2),
            (10, 10, 10),
            (7, 0, 3),
            (5, 0),)

        for contig, bins_contig, weighted, density, shape in \
                product([True, False], [True, False], [True, False], [True, False], shapes):
            D = shape[-1]

            values = make_tensor(shape, dtype=dtype, device=device, low=-9, high=9, noncontiguous=not contig)
            weights = (
                make_tensor(shape[:-1], dtype=dtype, device=device, low=0, high=9, noncontiguous=not contig)
                if weighted
                else None
            )

            # Tests passing a single bin count
            bin_ct = random.randint(1, 5)
            self._test_histogramdd_numpy(values, bin_ct, None, weights, density)

            # Tests passing a bin count for each dimension
            bin_ct = [random.randint(1, 5) for dim in range(D)]
            self._test_histogramdd_numpy(values, bin_ct, None, weights, density)

            # Tests with caller-specified histogram range
            bin_range_tuples = [sorted((random.uniform(-9, 9), random.uniform(-9, 9))) for dim in range(D)]
            bin_range = [elt for t in bin_range_tuples for elt in t]
            self._test_histogramdd_numpy(values, bin_ct, bin_range, weights, density)

            # Tests with range min=max
            for dim in range(D):
                bin_range[2 * dim + 1] = bin_range[2 * dim]
            self._test_histogramdd_numpy(values, bin_ct, bin_range, weights, density)

            # Tests with caller-specified bin edges
            bin_edges = [make_tensor(ct + 1, dtype=dtype, device=device, low=-9, high=9).msort() for ct in bin_ct]
            if not bins_contig:
                # Necessary because msort always produces contiguous output
                bin_edges_noncontig = [
                    make_tensor(ct + 1, dtype=dtype, device=device, noncontiguous=not bins_contig)
                    for ct in bin_ct
                ]
                for dim in range(D):
                    bin_edges_noncontig[dim].copy_(bin_edges[dim])
                bin_edges = bin_edges_noncontig
            for dim in range(D):
                self.assertEqual(bin_edges[dim].is_contiguous(), bins_contig)
            self._test_histogramdd_numpy(values, bin_edges, None, weights, density)