def test_reduction_vectorize_along_input_corner(self, device, dtype):
        # 1D case: sum
        size = 1024 * 1024 * 64 + 3
        shift = 1
        x = torch.zeros(size, dtype=dtype, device=device)
        y = x[shift:]
        for i in range(100):
            x.zero_()
            x[i] = 1
            self.assertEqual(x.sum(), 1.0)
            if i < shift:
                self.assertEqual(y.sum(), 0.0)
            else:
                self.assertEqual(y.sum(), 1.0)
        for i in range(1, 100):
            x.zero_()
            x[-i] = 1
            self.assertEqual(x.sum(), 1.0)
            self.assertEqual(y.sum(), 1.0)
        # 1D case: argmax
        size = 1024 * 1024 * 64 + 3
        shift = 1
        ysize = size - shift
        x = torch.zeros(size, dtype=dtype, device=device)
        y = x[shift:]
        for i in range(100):
            x.zero_()
            x[i] = 1
            self.assertEqual(x.argmax().item(), i)
            if i >= shift:
                self.assertEqual(y.argmax().item(), i - shift)
        for i in range(1, 100):
            x.zero_()
            x[-i] = 1
            self.assertEqual(x.argmax().item(), size - i)
            self.assertEqual(y.argmax().item(), ysize - i)
        # 2D case: sum
        size = (7, 1024 * 1024 + 3)
        x = torch.zeros(size, dtype=dtype, device=device)
        for i in range(100):
            x.zero_()
            for j in range(7):
                x[j][i] = j
            xs = x.sum(dim=-1)
            for j in range(7):
                self.assertEqual(xs[j].item(), float(j))
        for i in range(100):
            x.zero_()
            for j in range(7):
                x[j][-i] = j
            xs = x.sum(dim=-1)
            for j in range(7):
                self.assertEqual(xs[j].item(), float(j))
        # 2D case: max/argmax
        size = (7, 1024 * 1024 + 3)
        x = torch.zeros(size, dtype=dtype, device=device)
        for i in range(100):
            x.zero_()
            for j in range(7):
                x[j][i] = j + 1
            xs1 = x.argmax(dim=-1)
            xs2 = x.max(dim=-1).indices
            for j in range(7):
                self.assertEqual(xs1[j].item(), i)
                self.assertEqual(xs2[j].item(), i)
        for i in range(1, 100):
            x.zero_()
            for j in range(7):
                x[j][-i] = j + 1
            xs1 = x.argmax(dim=-1)
            xs2 = x.max(dim=-1).indices
            for j in range(7):
                self.assertEqual(xs1[j].item(), size[1] - i)
                self.assertEqual(xs2[j].item(), size[1] - i)
        # 2D case: min/argmin
        size = (7, 1024 * 1024 + 3)
        x = torch.zeros(size, dtype=dtype, device=device)
        for i in range(100):
            x.zero_()
            for j in range(7):
                x[j][i] = -(j + 1)
            xs1 = x.argmin(dim=-1)
            xs2 = x.min(dim=-1).indices
            for j in range(7):
                self.assertEqual(xs1[j].item(), i)
                self.assertEqual(xs2[j].item(), i)
        for i in range(1, 100):
            x.zero_()
            for j in range(7):
                x[j][-i] = -(j + 1)
            xs1 = x.argmin(dim=-1)
            xs2 = x.min(dim=-1).indices
            for j in range(7):
                self.assertEqual(xs1[j].item(), size[1] - i)
                self.assertEqual(xs2[j].item(), size[1] - i)