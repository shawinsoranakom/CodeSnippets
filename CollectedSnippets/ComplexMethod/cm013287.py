def _test_ddp_native_mixed_precision(
            self, gradient_as_bucket_view, set_grad_to_none
        ):
            rank = self.rank
            torch.manual_seed(rank)
            torch.cuda.manual_seed(rank)
            torch.cuda.set_device(rank)
            inp = torch.randn(10, 1)
            mp_config = self._get_fp16_config()

            class MyModel(torch.nn.Module):
                def __init__(self) -> None:
                    super().__init__()
                    self.m = torch.nn.Linear(1, 5)
                    self.register_buffer("buffer", torch.randn(1, 2))
                    self.p = torch.nn.Parameter(torch.randn(10, 5), requires_grad=False)

                def forward(self_, x):
                    params = self_.m.parameters()
                    for p in params:
                        self.assertEqual(mp_config.param_dtype, p.dtype)

                    self.assertEqual(self_.buffer.dtype, mp_config.buffer_dtype)

                    self.assertEqual(mp_config.param_dtype, x.dtype)
                    return self_.m(x) + self_.p

            m = MyModel()

            net = torch.nn.parallel.DistributedDataParallel(
                m.to(rank),
                device_ids=[rank],
                mixed_precision=mp_config,
                gradient_as_bucket_view=gradient_as_bucket_view,
            )
            # Buffers are casted in constructor.
            self.assertEqual(net.module.buffer.dtype, mp_config.buffer_dtype)
            # Each param should have an mp_param in the lower precision, and
            # an fp_param in the higher precision.
            for p in net.parameters():
                self.assertEqual(mp_config.param_dtype, p._mp_param.dtype)
                self.assertEqual(torch.float32, p._fp_param.dtype)

            for _ in range(6):
                loss = net(inp).sum()
                loss.backward()
                # Verify gradient synchronization and params and grads are fp32.
                for n, param in net.named_parameters():
                    self.assertEqual(param.dtype, torch.float32)
                    if param.grad is None:
                        if n != "module.p":  # Only param that doesn't require grad
                            raise AssertionError(f"Expected n == 'module.p', got {n!r}")
                    else:
                        self.assertEqual(param.grad.dtype, torch.float32)
                        tensor_list = [
                            torch.zeros_like(param.grad)
                            for _ in range(dist.get_world_size(net.process_group))
                        ]
                        dist.all_gather(tensor_list, param.grad)
                        g, rest = tensor_list[0], tensor_list[1:]
                        self.assertEqual(g.dtype, torch.float32)
                        for g_ in rest:
                            self.assertEqual(g_.dtype, torch.float32)
                            self.assertEqual(g, g_)
                net.zero_grad(set_to_none=set_grad_to_none)