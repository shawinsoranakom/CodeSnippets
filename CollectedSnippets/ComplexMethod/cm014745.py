def test_clip_grad_norm(self, norm_type, foreach, device):
        if torch.device(device).type == 'xla' and foreach:
            raise SkipTest('foreach not supported on XLA')
        if torch.device(device).type == 'mps' and foreach:
            raise SkipTest('foreach not supported on MPS')

        l = nn.Linear(10, 10).to(device)
        max_norm = 2

        def compute_norm(norm_type):
            norm_type = float(norm_type)
            if norm_type != inf:
                total_norm = 0
                for p in l.parameters():
                    total_norm += p.grad.data.abs().pow(norm_type).sum()
                return pow(total_norm, 1. / norm_type)
            else:
                return max(p.grad.data.abs().max() for p in l.parameters())

        def compare_scaling(grads):
            p_scale = [p.grad.data.div(g).view(-1) for p, g in zip(l.parameters(), grads)]
            scale = torch.cat(p_scale)
            self.assertEqual(scale.std(), 0)
            return scale[0]

        grads = torch.arange(1., 101, device=device).view(10, 10), torch.ones(10, device=device).div(1000)
        for p, g in zip(l.parameters(), grads):
            p._grad = g.clone().view_as(p.data)
        norm_before = compute_norm(norm_type)
        norm = clip_grad_norm_(l.parameters(), max_norm, norm_type=norm_type, foreach=foreach)
        norm_after = compute_norm(norm_type)
        self.assertEqual(norm, norm_before)
        self.assertEqual(norm_after, max_norm)
        self.assertLessEqual(norm_after, norm_before)
        compare_scaling(grads)

        # decomposed APIs should behave as expected
        grads = torch.arange(1., 101, device=device).view(10, 10), torch.ones(10, device=device).div(1000)
        for p, g in zip(l.parameters(), grads):
            p._grad = g.clone().view_as(p)
        norm_before = compute_norm(norm_type)
        grads = [p.grad for p in l.parameters()]
        total_norm = get_total_norm(grads, norm_type=norm_type, foreach=foreach)
        clip_grads_with_norm_(l.parameters(), max_norm, total_norm, foreach=foreach)
        norm_after = compute_norm(norm_type)
        self.assertEqual(total_norm, norm_before)
        self.assertEqual(norm_after, max_norm)
        self.assertLessEqual(norm_after, norm_before)
        compare_scaling(grads)

        # Small gradients should be left unchanged
        grads = torch.rand(10, 10, device=device).div(10000), torch.ones(10, device=device).div(500)
        for p, g in zip(l.parameters(), grads):
            p.grad.data.copy_(g)
        norm_before = compute_norm(norm_type)
        norm = clip_grad_norm_(l.parameters(), max_norm, norm_type=norm_type, foreach=foreach)
        norm_after = compute_norm(norm_type)
        self.assertEqual(norm, norm_before)
        self.assertEqual(norm_before, norm_after)
        self.assertLessEqual(norm_after, max_norm)
        scale = compare_scaling(grads)
        self.assertEqual(scale, 1)

        # Should accept a single Tensor as input
        p1, p2 = torch.randn(10, 10, device=device), torch.randn(10, 10, device=device)
        g = torch.arange(1., 101, device=device).view(10, 10)
        p1._grad = g.clone()
        p2._grad = g.clone()
        clip_grad_norm_(p1, max_norm, norm_type=norm_type, foreach=foreach)
        clip_grad_norm_([p2], max_norm, norm_type=norm_type, foreach=foreach)
        self.assertEqual(p1.grad, p2.grad)

        # Should warning when parameters generator exhausted
        params = l.parameters()
        for _p in params:
            pass
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            clip_grad_norm_(params, max_norm, norm_type=norm_type, foreach=foreach)
            self.assertEqual(len(w), 1)
            self.assertEqual(str(w[0].message), "`parameters` is an empty generator, no gradient clipping will occur.")