def test_batchnorm_e2e(self):
        class Repro(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.bn = torch.nn.BatchNorm2d(
                    64, eps=1e-05, momentum=0.1, affine=True, track_running_stats=True
                )
                self.conv1 = torch.nn.Conv2d(
                    64,
                    64,
                    kernel_size=(3, 3),
                    stride=(1, 1),
                    padding=(1, 1),
                    bias=False,
                )

            def forward(self, x):
                x1 = self.bn(x)
                x2 = self.conv1(x1)
                out = torch.nn.functional.relu(x2)
                return (out,)

        torch.manual_seed(1337)

        m_ref = Repro()
        m_test = deepcopy(m_ref)

        @torch.compile(backend="aot_eager_decomp_partition")
        def compiled_fn(x):
            return m_test(x)

        x_ref = torch.randn(2, 64, 32, 32, requires_grad=True)
        x_test = x_ref.clone()

        # Loop multiple times: each iteration the running_mean/var on batchnorm will update,
        # which changes the output of the next iteration
        for _ in range(3):
            ref = m_ref(x_ref)
            res = compiled_fn(x_test)

            self.assertTrue(same(ref, res))

            for r in ref:
                if r.requires_grad:
                    r.sum().backward()
            for r in res:
                if r.requires_grad:
                    r.sum().backward()

            for param_ref, param_test in zip(m_ref.parameters(), m_test.parameters()):
                self.assertTrue(same(param_ref, param_test))
            # Assert running_mean/var
            for buffer_ref, buffer_test in zip(m_ref.buffers(), m_test.buffers()):
                self.assertTrue(same(buffer_ref, buffer_test))