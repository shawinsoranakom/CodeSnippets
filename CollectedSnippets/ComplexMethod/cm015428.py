def test_strided_grad_layout(self):
        class ConvNet(nn.Module):
            def __init__(self, layouts, dtype_list):
                super().__init__()
                self.dtypes = dtype_list
                self.conv0 = torch.nn.Conv2d(8, 16, (2, 2)).to(
                    memory_format=layouts[0], dtype=dtype_list[0]
                )
                self.conv1 = torch.nn.Conv2d(16, 32, (2, 2)).to(
                    memory_format=layouts[1], dtype=dtype_list[1]
                )
                self.conv2 = torch.nn.Conv2d(32, 16, (2, 2)).to(
                    memory_format=layouts[2], dtype=dtype_list[2]
                )
                self.conv3 = torch.nn.Conv2d(16, 8, (2, 2)).to(
                    memory_format=layouts[3], dtype=dtype_list[3]
                )

            def forward(self, x):
                x = x.to(self.dtypes[0])
                x = self.conv0(x).to(self.dtypes[1])
                x = self.conv1(x).to(self.dtypes[2])
                x = self.conv2(x).to(self.dtypes[3])
                x = self.conv3(x)
                return x

        layer_formats = (
            [torch.contiguous_format] * 4,
            [torch.channels_last] * 2 + [torch.contiguous_format] * 2,
            [torch.channels_last] * 4,
        )
        layer_dtypes = (
            [torch.float] * 4,
            [torch.float] * 2 + [torch.half] * 2,
            [torch.half] * 4,
        )

        ndevs = torch.cuda.device_count()
        input = torch.randn(ndevs * 8, 8, 8, 8, device="cuda:0", dtype=torch.float)
        target = torch.randn(ndevs * 8, 8, 4, 4, device="cuda:0", dtype=torch.float)
        device_ids = list(range(ndevs))

        with torch.backends.cudnn.flags(
            enabled=True, deterministic=True, benchmark=False
        ):
            for formats, dtype_list in product(layer_formats, layer_dtypes):
                model_msg = f"formats = {formats} dtypes = {dtypes}"
                try:
                    m = ConvNet(formats, dtype_list).cuda(device="cuda:0")
                    m_dp = dp.DataParallel(deepcopy(m), device_ids=device_ids)
                    opt = torch.optim.SGD(m.parameters(), lr=0.1)
                    opt_dp = torch.optim.SGD(m_dp.parameters(), lr=0.1)
                    has_half = any(p.dtype is torch.half for p in m.parameters())
                    tol = 3.0e-3 if has_half else 1.0e-5
                except BaseException:
                    # Prints case-specific debugging info to narrow down failing case.
                    print(
                        "Caught exception during model creation for " + model_msg,
                        flush=True,
                    )
                    raise
                # 2 iters:  First iter creates grads, second iter tries zeroed grads.
                for it in range(2):
                    iter_msg = f"iter = {it} " + model_msg
                    named_msg = iter_msg
                    try:
                        F.mse_loss(m(input).float(), target).backward()
                        F.mse_loss(m_dp(input).float(), target).backward()
                        for i, ((layer_name, m_child), m_dp_child) in enumerate(
                            zip(m.named_children(), m_dp.module.children())
                        ):
                            named_msg = layer_name + ".weight " + iter_msg
                            self.assertTrue(
                                m_child.weight.grad.is_contiguous(
                                    memory_format=formats[i]
                                ),
                                named_msg,
                            )
                            self.assertTrue(
                                m_dp_child.weight.grad.is_contiguous(
                                    memory_format=formats[i]
                                ),
                                named_msg,
                            )
                            for (param_name, p), p_dp in zip(
                                m_child.named_parameters(), m_dp_child.parameters()
                            ):
                                named_msg = (
                                    layer_name + "." + param_name + " " + iter_msg
                                )
                                self.assertEqual(p.grad, p_dp.grad, rtol=tol, atol=tol)
                        opt.step()
                        opt_dp.step()
                        opt.zero_grad()
                        opt_dp.zero_grad()
                    except BaseException:
                        # Makes sure we still get info if an error occurred somewhere other than the asserts.
                        print(
                            "Caught exception during iterations at " + named_msg,
                            flush=True,
                        )
                        raise