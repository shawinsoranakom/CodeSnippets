def test_clip_grad_value(self, foreach, device):
        if torch.device(device).type == 'xla' and foreach:
            raise SkipTest('foreach not supported on XLA')
        if torch.device(device).type == 'mps' and foreach:
            raise SkipTest('foreach not supported on MPS')

        l = nn.Linear(10, 10).to(device)
        clip_value = 2.5

        grad_w, grad_b = torch.arange(-50., 50, device=device).view(10, 10).div_(5), torch.ones(10, device=device).mul_(2)
        for grad_list in [[grad_w, grad_b], [grad_w, None]]:
            for p, g in zip(l.parameters(), grad_list):
                p._grad = g.clone().view_as(p.data) if g is not None else g

            clip_grad_value_(l.parameters(), clip_value, foreach=foreach)
            for p in filter(lambda p: p.grad is not None, l.parameters()):
                self.assertLessEqual(p.grad.data.max(), clip_value)
                self.assertGreaterEqual(p.grad.data.min(), -clip_value)

        # Should accept a single Tensor as input
        p1, p2 = torch.randn(10, 10, device=device), torch.randn(10, 10, device=device)
        g = torch.arange(-50., 50, device=device).view(10, 10).div_(5)
        p1._grad = g.clone()
        p2._grad = g.clone()
        clip_grad_value_(p1, clip_value, foreach=foreach)
        clip_grad_value_([p2], clip_value, foreach=foreach)
        self.assertEqual(p1.grad, p2.grad)