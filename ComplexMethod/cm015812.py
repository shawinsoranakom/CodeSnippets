def test_conv_bn_eval(
            test_class, use_bias, module, sync_bn, decompose_nn_module
        ):
            from functorch import make_fx
            from torch._dispatch.python import enable_python_dispatcher

            kwargs = {"kernel_size": 3, "stride": 2} if module[0] != nn.Linear else {}
            mod_eager = test_class(
                module[0],
                module[1],
                use_bias,
                3,
                32,
                self.device,
                **kwargs,
            ).eval()
            # Copy module to test backward
            mod_optimized = copy.deepcopy(mod_eager)
            if sync_bn:
                mod_eager = nn.SyncBatchNorm.convert_sync_batchnorm(mod_eager).eval()
                mod_optimized = nn.SyncBatchNorm.convert_sync_batchnorm(
                    mod_optimized
                ).eval()
            torch._dynamo.reset()

            inps = [4, 3]
            # Conv shape goes from big to small, and ConvTranspose shape goes from small to big
            spatial_d = (
                4 if issubclass(module[0], nn.modules.conv._ConvTransposeNd) else 96
            )
            if module[0] is nn.Conv1d or module[0] is nn.ConvTranspose1d:
                inps += [spatial_d] * 1
            if module[0] is nn.Conv2d or module[0] is nn.ConvTranspose2d:
                inps += [spatial_d] * 2
            if module[0] is nn.Conv3d or module[0] is nn.ConvTranspose3d:
                inps += [spatial_d] * 3
            inp = torch.rand(inps).to(self.device)

            if decompose_nn_module:
                with enable_python_dispatcher():
                    mod_optimized = make_fx(mod_optimized, pre_dispatch=True)(inp)
            mod_optimized = torch.compile(mod_optimized)

            original_value = counters["inductor"]["efficient_conv_bn_eval"]

            optim_eager = torch.optim.SGD(mod_eager.parameters(), lr=1e-3)
            optim_optimized = torch.optim.SGD(mod_optimized.parameters(), lr=1e-3)

            optim_eager.zero_grad()
            optim_optimized.zero_grad()

            # test forward
            out_eager = mod_eager(inp)
            out_optimized = mod_optimized(inp)

            self.assertEqual(out_optimized, out_eager)

            out_eager.mean().backward()
            out_optimized.mean().backward()

            optim_eager.step()
            optim_optimized.step()
            # test forward (by testing forward again after one training iteration)
            inp_bw = torch.rand_like(inp)
            out_eager_bw = mod_eager(inp_bw)
            out_optimized_bw = mod_optimized(inp_bw)

            self.assertEqual(out_eager_bw, out_optimized_bw)
            current_value = counters["inductor"]["efficient_conv_bn_eval"]
            self.assertEqual(
                current_value - original_value, test_class.expected_optimization_count
            )