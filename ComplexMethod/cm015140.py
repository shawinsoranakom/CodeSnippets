def test_split_with_sizes_copy_out(self):
        device = torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")
        shape = (30, 40, 50)
        x = torch.rand(*shape, device=device)
        cases = [
            (0, [3, 7, 8, 12]),
            (1, [3, 7, 10, 20]),
            (-2, [3, 7, 10, 20]),
            (2, [3, 7, 10, 12, 18]),
            (-1, [3, 7, 10, 12, 18]),
            (2, [3, 7, 10, 0, 30]),
        ]
        for dim, split_sizes in cases:
            views = x.split_with_sizes(split_sizes, dim=dim)
            expects = [v.clone() for v in views]
            out = [torch.zeros_like(v) for v in views]
            for expect, t in zip(expects, out):
                if expect.numel() != 0:
                    self.assertFalse(expect.eq(t).all().item())

            torch.split_with_sizes_copy(x, split_sizes, dim=dim, out=out)
            for expect, t in zip(expects, out):
                self.assertTrue(expect.eq(t).all().item())

            if not torch.cuda.is_available():
                continue

            # Test with cuda graph
            out = [torch.zeros_like(v) for v in views]
            for expect, t in zip(expects, out):
                if expect.numel() != 0:
                    self.assertFalse(expect.eq(t).all().item())

            g = torch.cuda.CUDAGraph()
            with torch.cuda.graph(g):
                torch.split_with_sizes_copy(x, split_sizes, dim=dim, out=out)

            g.replay()
            for expect, t in zip(expects, out):
                self.assertTrue(expect.eq(t).all().item())